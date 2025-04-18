#!/usr/bin/env python3
"""
preprocess_audio.py

Preprocess a WAV audio file into frame‐level brightness & note color CSV.

Usage:
  1. Convert MP3 to WAV (once), e.g. with pydub or Audacity:
       from pydub import AudioSegment
       song = AudioSegment.from_mp3("Really_Love.mp3")
       song.export("really_love.wav", format="wav")
  2. Run this script:
       python3 preprocess_audio.py \
         --input really_love.wav \
         --output really_love_frames.csv \
         --frame_duration 0.04 \
         --overlap 0.5 \
         --rms_threshold 0.02
"""

import os
import sys
import argparse
import logging

import numpy as np
import pandas as pd
import librosa
from pydub import AudioSegment
song = AudioSegment.from_mp3("Really_Love.mp3")
song.export("really_love.wav", format="wav")

# Default settings
DEFAULT_INPUT_WAV   = "really_love.wav"
DEFAULT_OUTPUT_CSV  = "really_love_frames.csv"
DEFAULT_FRAME_SEC   = 0.04     # 40 ms
DEFAULT_OVERLAP     = 0.5      # 50% overlap
DEFAULT_RMS_THRESH  = 0.02     # 2% of max RMS

NOTE_COLORS = {
    'C': (255,   0,   0),  # Red
    'D': (255, 128,   0),  # Orange
    'E': (255, 255,   0),  # Yellow
    'F': (  0, 255,   0),  # Green
    'G': (  0, 255, 255),  # Cyan
    'A': (  0,   0, 255),  # Blue
    'B': (128,   0, 255),  # Violet
}

def freq_to_note(freq):
    """Map frequency (Hz) → note letter (C–B), or None."""
    if np.isnan(freq):
        return None
    # Get note name without octave (e.g. "C#", "D")
    note_name = librosa.hz_to_note(freq, octave=False)
    letter = note_name[0]
    return letter if letter in NOTE_COLORS else None

def parse_args():
    p = argparse.ArgumentParser(description="Audio → brightness, note & RGB CSV")
    p.add_argument("-i", "--input",        default=DEFAULT_INPUT_WAV,
                   help="Input WAV file")
    p.add_argument("-o", "--output",       default=DEFAULT_OUTPUT_CSV,
                   help="Output CSV file")
    p.add_argument("-f", "--frame_duration", type=float, default=DEFAULT_FRAME_SEC,
                   help="Frame duration in seconds")
    p.add_argument("-l", "--overlap",      type=float, default=DEFAULT_OVERLAP,
                   help="Fractional overlap between frames (0–<1)")
    p.add_argument("-t", "--rms_threshold", type=float, default=DEFAULT_RMS_THRESH,
                   help="Ignore pitch if RMS < this fraction of max")
    return p.parse_args()

def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s %(levelname)s: %(message)s")

    # Validate input file
    if not os.path.isfile(args.input):
        logging.error(f"Input file not found: {args.input}")
        sys.exit(1)

    logging.info(f"Loading audio: {args.input}")
    y, sr = librosa.load(args.input, sr=None)
    frame_len = int(args.frame_duration * sr)
    hop_len   = int(frame_len * (1.0 - args.overlap))
    if hop_len < 1:
        logging.warning("Overlap too high → setting hop_len = 1 sample")
        hop_len = 1

    # Compute RMS
    logging.info("Computing RMS energy")
    rms = librosa.feature.rms(y=y, frame_length=frame_len, hop_length=hop_len)[0]
    times = librosa.frames_to_time(np.arange(len(rms)), sr=sr, hop_length=hop_len)
    max_rms = rms.max()
    thresh  = max_rms * args.rms_threshold
    logging.info(f"Max RMS={max_rms:.6f}, pitch threshold={thresh:.6f}")

    # Pitch detection via YIN
    logging.info("Detecting pitch (YIN)")
    f0 = librosa.yin(
        y,
        fmin=librosa.note_to_hz('C2'),
        fmax=librosa.note_to_hz('C7'),
        frame_length=frame_len,
        hop_length=hop_len
    )

    # Build frame data
    records = []
    for idx, (t, amp, freq) in enumerate(zip(times, rms, f0)):
        # Log‐scale brightness
        bright = int(np.interp(np.log1p(amp),
                               [0, np.log1p(max_rms)],
                               [0, 255]))
        note = freq_to_note(freq) if amp >= thresh else None
        if note:
            r, g, b = NOTE_COLORS[note]
        else:
            r, g, b = 0, 0, 0

        records.append({
            "frame":      idx,
            "time_sec":  round(float(t), 3),
            "brightness": bright,
            "note":       note or "None",
            "R":          r,
            "G":          g,
            "B":          b
        })

    # Save to CSV
    df = pd.DataFrame(records)
    df.to_csv(args.output, index=False)
    logging.info(f"Saved {len(df)} frames → {args.output}")

if __name__ == "__main__":
    main()
