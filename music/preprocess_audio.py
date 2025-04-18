#!/usr/bin/env python3
"""
preprocess_audio.py

Offline preprocess a WAV into frame‐level brightness & note color CSV,
manually computing RMS and using aubio’s streaming YIN pitch detector.

Dependencies:
  sudo apt install libaubio5           # system dependency
  pip3 install numpy pandas librosa aubio

Usage:
  python3 preprocess_audio.py \
    --input really_love.wav \
    --output really_love_frames.csv \
    --sr 8000 \
    --frame_duration 0.04 \
    --overlap 0.5 \
    --rms_threshold 0.02
"""
import os, sys, argparse, logging, math
import numpy as np
import pandas as pd
import librosa
from aubio import source, pitch as AubioPitch

# Defaults
DEFAULT_INPUT   = "really_love.wav"
DEFAULT_OUTPUT  = "really_love_frames.csv"
DEFAULT_SR      = 8000      # downsample to 8 kHz
DEFAULT_FRAME   = 0.04      # 40 ms
DEFAULT_OVERLAP = 0.5       # 50%
DEFAULT_THRESH  = 0.02      # 2% of peak RMS

NOTE_COLORS = {
  'C': (255,0,0), 'D': (255,128,0), 'E': (255,255,0),
  'F': (0,255,0), 'G': (0,255,255), 'A': (0,0,255),
  'B': (128,0,255),
}

def freq_to_note(freq):
    if freq <= 0 or math.isnan(freq):
        return None
    nm = librosa.hz_to_note(freq, octave=False)
    return nm[0] if nm[0] in NOTE_COLORS else None

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("-i","--input",       default=DEFAULT_INPUT,  help="Input WAV")
    p.add_argument("-o","--output",      default=DEFAULT_OUTPUT, help="Output CSV")
    p.add_argument("--sr", type=int,     default=DEFAULT_SR,    help="Resample Hz")
    p.add_argument("-f","--frame_duration", type=float, default=DEFAULT_FRAME, help="Frame length s")
    p.add_argument("-l","--overlap",     type=float, default=DEFAULT_OVERLAP, help="Overlap frac")
    p.add_argument("-t","--rms_threshold", type=float, default=DEFAULT_THRESH, help="RMS threshold frac")
    return p.parse_args()

def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    if not os.path.isfile(args.input):
        logging.error("Missing WAV: %s", args.input); sys.exit(1)

    # Load & downsample
    logging.info("Loading %s at %d Hz", args.input, args.sr)
    y, sr = librosa.load(args.input, sr=args.sr)

    # Compute frame/hop sizes
    frame_len = int(args.frame_duration * sr)
    hop_len   = max(1, int(frame_len * (1.0 - args.overlap)))
    n_frames  = 1 + max(0, (len(y) - frame_len)//hop_len)
    logging.info("Processing %d frames (frame_len=%d, hop_len=%d)", n_frames, frame_len, hop_len)

    # 1) RMS per frame
    rms_vals = np.empty(n_frames, dtype=float)
    for i in range(n_frames):
        win = y[i*hop_len : i*hop_len + frame_len]
        if len(win) < frame_len:
            win = np.pad(win, (0, frame_len - len(win)))
        rms_vals[i] = math.sqrt(np.mean(win*win))
    max_r = float(rms_vals.max())
    thresh = max_r * args.rms_threshold
    logging.info("Max RMS=%.6f, threshold=%.6f", max_r, thresh)

    # 2) Pitch via aubio source & pitch
    logging.info("Detecting pitch via Aubio YIN")
    src    = source(args.input, samplerate=sr, hop_size=hop_len)
    pitch_o= AubioPitch("yin", frame_len, hop_len, sr)
    pitch_o.set_unit("Hz")
    pitch_o.set_silence(-40)

    f0_vals = []
    while True:
        samples, read = src()
        if read < hop_len:
            break
        f0_vals.append(pitch_o(samples)[0])
    # Trim or pad to n_frames
    f0_vals = (f0_vals + [0]*n_frames)[:n_frames]

    # 3) Assemble CSV rows
    rows = []
    for idx in range(n_frames):
        t      = round((idx*hop_len)/sr, 3)
        amp    = rms_vals[idx]
        bright = int(np.interp(math.log1p(amp), [0, math.log1p(max_r)], [0,255]))
        note   = freq_to_note(f0_vals[idx]) if amp >= thresh else None
        r,g,b  = NOTE_COLORS[note] if note else (0,0,0)
        rows.append({
            "frame": idx,
            "time_sec": t,
            "brightness": bright,
            "note": note or "None",
            "R": r, "G": g, "B": b
        })

    # 4) Save CSV
    df = pd.DataFrame(rows)
    df.to_csv(args.output, index=False)
    logging.info("Saved %d frames → %s", len(df), args.output)

if __name__=="__main__":
    main()
