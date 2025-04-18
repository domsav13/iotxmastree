#!/usr/bin/env python3
"""
preprocess_audio.py

Preprocess a WAV audio file into frame‑level brightness & note color CSV,
downsampling heavily (default 8 kHz) to avoid memory limits.

Usage:
  python3 preprocess_audio.py \
    --input really_love.wav \
    --output really_love_frames.csv \
    --sr 8000 \
    --frame_duration 0.04 \
    --overlap 0.5 \
    --rms_threshold 0.02
"""

import os
import sys
import argparse
import logging
import math

import numpy as np
import pandas as pd
import librosa

# Defaults
DEFAULT_INPUT_WAV   = "really_love.wav"
DEFAULT_OUTPUT_CSV  = "really_love_frames.csv"
DEFAULT_SR          = 8000
DEFAULT_FRAME_SEC   = 0.04
DEFAULT_OVERLAP     = 0.5
DEFAULT_RMS_THRESH  = 0.02

NOTE_COLORS = {
    'C': (255,   0,   0),
    'D': (255, 128,   0),
    'E': (255, 255,   0),
    'F': (  0, 255,   0),
    'G': (  0, 255, 255),
    'A': (  0,   0, 255),
    'B': (128,   0, 255),
}

def freq_to_note(freq):
    if np.isnan(freq):
        return None
    nm = librosa.hz_to_note(freq, octave=False)
    return nm[0] if nm[0] in NOTE_COLORS else None

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("-i","--input",      default=DEFAULT_INPUT_WAV, help="Input WAV")
    p.add_argument("-o","--output",     default=DEFAULT_OUTPUT_CSV, help="Output CSV")
    p.add_argument("--sr", type=int,    default=DEFAULT_SR,         help="Resample rate (Hz)")
    p.add_argument("-f","--frame_duration", type=float, default=DEFAULT_FRAME_SEC, help="Frame length (s)")
    p.add_argument("-l","--overlap",    type=float, default=DEFAULT_OVERLAP,    help="Overlap fraction")
    p.add_argument("-t","--rms_threshold", type=float, default=DEFAULT_RMS_THRESH, help="RMS threshold frac")
    return p.parse_args()

def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    if not os.path.isfile(args.input):
        logging.error("WAV not found: %s", args.input)
        sys.exit(1)

    logging.info("Loading audio at %d Hz: %s", args.sr, args.input)
    y, sr = librosa.load(args.input, sr=args.sr)

    frame_len = int(args.frame_duration * sr)
    hop_len   = int(frame_len * (1.0 - args.overlap))
    if hop_len < 1:
        logging.warning("Overlap too high; forcing hop_len=1")
        hop_len = 1

    n_frames = 1 + max(0, (len(y) - frame_len) // hop_len)
    logging.info("Computing RMS over %d frames", n_frames)
    rms = np.empty(n_frames, dtype=float)
    times = np.empty(n_frames, dtype=float)
    for i in range(n_frames):
        start = i * hop_len
        win = y[start:start+frame_len]
        rms[i] = math.sqrt(np.mean(win*win)) if len(win) == frame_len else 0.0
        times[i] = start / sr
    max_r = float(rms.max())
    thresh = max_r * args.rms_threshold
    logging.info("Max RMS=%.6f, threshold=%.6f", max_r, thresh)

    logging.info("Detecting pitch with YIN")
    f0 = librosa.yin(
        y,
        fmin=librosa.note_to_hz('C2'),
        fmax=librosa.note_to_hz('C7'),
        sr=sr,                    # <--- tell YIN the actual sample rate
        frame_length=frame_len,
        hop_length=hop_len
    )

    records = []
    for idx, (t, amp, freq) in enumerate(zip(times, rms, f0)):
        bright = int(np.interp(np.log1p(amp), [0, np.log1p(max_r)], [0, 255]))
        note = freq_to_note(freq) if amp >= thresh else None
        r,g,b = NOTE_COLORS[note] if note else (0,0,0)
        records.append({
            "frame":      idx,
            "time_sec":  round(float(t), 3),
            "brightness": bright,
            "note":       note or "None",
            "R":          r,
            "G":          g,
            "B":          b
        })

    df = pd.DataFrame(records)
    df.to_csv(args.output, index=False)
    logging.info("Saved %d frames → %s", len(df), args.output)

if __name__ == "__main__":
    main()
