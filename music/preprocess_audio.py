#!/usr/bin/env python3
"""
preprocess_audio.py

Offline preprocess a WAV into frame‑level brightness & note color CSV,
computing RMS and YIN pitch per‑frame to avoid huge buffers.

Dependencies:
  pip3 install numpy pandas librosa aubio
  sudo apt install libaubio5  # or pip3 install aubio

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
from aubio import pitch as AubioPitch

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
    if np.isnan(freq) or freq <= 0:
        return None
    nm = librosa.hz_to_note(freq, octave=False)
    return nm[0] if nm[0] in NOTE_COLORS else None

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("-i","--input", default=DEFAULT_INPUT, help="Input WAV")
    p.add_argument("-o","--output", default=DEFAULT_OUTPUT, help="Output CSV")
    p.add_argument("--sr", type=int, default=DEFAULT_SR, help="Resample Hz")
    p.add_argument("-f","--frame_duration", type=float, default=DEFAULT_FRAME, help="Frame length s")
    p.add_argument("-l","--overlap", type=float, default=DEFAULT_OVERLAP, help="Overlap frac")
    p.add_argument("-t","--rms_threshold", type=float, default=DEFAULT_THRESH, help="RMS threshold frac")
    return p.parse_args()

def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    if not os.path.isfile(args.input):
        logging.error("Missing input WAV: %s", args.input); sys.exit(1)

    logging.info("Loading %s at %d Hz", args.input, args.sr)
    y, sr = librosa.load(args.input, sr=args.sr)

    frame_len = int(args.frame_duration * sr)
    hop_len   = int(frame_len * (1.0 - args.overlap)) or 1
    n_frames  = 1 + max(0, (len(y) - frame_len)//hop_len)
    logging.info("Processing %d frames (frame_len=%d, hop_len=%d)", n_frames, frame_len, hop_len)

    # Set up Aubio YIN detector
    pitch_o = AubioPitch("yin", frame_len, hop_len, sr)
    pitch_o.set_unit("Hz")
    pitch_o.set_silence(-40)  # ignore very quiet

    # First pass: compute RMS and collect windows
    records = []
    max_rms = 0.0
    windows = []
    for i in range(n_frames):
        start = i*hop_len
        w = y[start:start+frame_len]
        if len(w) < frame_len:
            w = np.pad(w, (0, frame_len-len(w)))
        windows.append(w)
        rms = math.sqrt(np.mean(w*w))
        max_rms = max(max_rms, rms)
        records.append({"rms":rms})
    thresh = max_rms * args.rms_threshold
    logging.info("Max RMS=%.6f, threshold=%.6f", max_rms, thresh)

    # Second pass: detect pitch per window
    for i, w in enumerate(windows):
        freq = pitch_o(w.astype(np.float32))[0]
        records[i]["freq"] = freq

    # Build final rows
    rows = []
    for idx, rec in enumerate(records):
        t = idx * hop_len / sr
        bright = int(np.interp(math.log1p(rec["rms"]),
                               [0, math.log1p(max_rms)],
                               [0,255]))
        note = freq_to_note(rec["freq"]) if rec["rms"]>=thresh else None
        r,g,b = NOTE_COLORS[note] if note else (0,0,0)
        rows.append({
            "frame": idx,
            "time_sec": round(t,3),
            "brightness": bright,
            "note": note or "None",
            "R":r, "G":g, "B":b
        })

    # Save CSV
    df = pd.DataFrame(rows)
    df.to_csv(args.output, index=False)
    logging.info("Saved %d frames → %s", len(df), args.output)

if __name__=="__main__":
    main()
