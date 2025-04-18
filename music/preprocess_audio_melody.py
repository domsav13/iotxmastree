#!/usr/bin/env python3
"""
preprocess_audio_melody.py

Extract frame‑level brightness & note color CSV for the song's main melody only,
without global HPSS (to avoid large buffers).

Dependencies:
  sudo apt install libaubio5
  pip3 install numpy pandas librosa aubio scipy

Usage:
  python3 preprocess_audio_melody.py \
    --input really_love.wav \
    --output really_love_melody.csv \
    --sr 8000 \
    --frame_duration 0.04 \
    --overlap 0.5 \
    --rms_threshold 0.05 \
    --hold \
    --alpha 0.3
"""
import os, sys, argparse, logging, math

import numpy as np
import pandas as pd
import librosa
from scipy.signal import medfilt
from aubio import source, pitch as AubioPitch

# Defaults
DEFAULT_INPUT      = "really_love.wav"
DEFAULT_OUTPUT     = "really_love_melody.csv"
DEFAULT_SR         = 8000     # downsample to 8 kHz
DEFAULT_FRAME_SEC  = 0.04
DEFAULT_OVERLAP    = 0.5
DEFAULT_THRESH     = 0.05     # gate RMS threshold
DEFAULT_HOLD       = False
DEFAULT_ALPHA      = 0.3      # brightness smoothing
MEDIAN_KERNEL_SIZE = 7        # must be odd

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
    if freq <= 0 or math.isnan(freq):
        return None
    nm = librosa.hz_to_note(freq, octave=False)
    return nm[0] if nm[0] in NOTE_COLORS else None


def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument("-i","--input",        default=DEFAULT_INPUT,      help="Input WAV")
    p.add_argument("-o","--output",       default=DEFAULT_OUTPUT,     help="Output CSV")
    p.add_argument("--sr", type=int,      default=DEFAULT_SR,         help="Resample rate")
    p.add_argument("-f","--frame_duration", type=float, default=DEFAULT_FRAME_SEC, help="Frame length (s)")
    p.add_argument("-l","--overlap",      type=float, default=DEFAULT_OVERLAP,   help="Overlap fraction")
    p.add_argument("-t","--rms_threshold", type=float, default=DEFAULT_THRESH,    help="Gate RMS threshold fraction")
    p.add_argument("--hold", action="store_true", default=DEFAULT_HOLD,         help="Hold last note forward")
    p.add_argument("--alpha", type=float, default=DEFAULT_ALPHA,                help="Brightness smoothing α")
    return p.parse_args()


def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s: %(message)s")

    if not os.path.isfile(args.input):
        logging.error("Missing WAV: %s", args.input)
        sys.exit(1)

    # 1) Load & downsample
    logging.info("Loading %s at %d Hz", args.input, args.sr)
    y, sr = librosa.load(args.input, sr=args.sr)

    # 2) Calculate frame/hop
    frame_len = int(args.frame_duration * sr)
    hop_len   = max(1, int(frame_len * (1.0 - args.overlap)))
    n_frames  = 1 + max(0, (len(y) - frame_len) // hop_len)
    logging.info("Frames: %d  (frame_len=%d, hop_len=%d)", n_frames, frame_len, hop_len)

    # 3) Compute RMS per frame
    rms_vals = np.empty(n_frames, dtype=float)
    for i in range(n_frames):
        w = y[i*hop_len : i*hop_len + frame_len]
        if len(w) < frame_len:
            w = np.pad(w, (0, frame_len - len(w)))
        rms_vals[i] = math.sqrt(np.mean(w*w))
    max_r = float(rms_vals.max())
    gate  = max_r * args.rms_threshold
    logging.info("Max RMS=%.6f  gate=%.6f", max_r, gate)

    # 4) Raw pitch detection (Aubio) on raw signal
    src     = source(args.input, samplerate=sr, hop_size=hop_len)
    pitch_o = AubioPitch("yin", frame_len, hop_len, sr)
    pitch_o.set_unit("Hz")
    pitch_o.set_silence(-40)

    f0_vals = []
    while True:
        buf, read = src()
        if read < hop_len:
            break
        f0_vals.append(float(pitch_o(buf)[0]))
    # pad/trim to length
    f0_vals = (f0_vals + [0]*n_frames)[:n_frames]

    # 5) Median‐filter the pitch to extract the melody contour
    f0_med = medfilt(f0_vals, kernel_size=MEDIAN_KERNEL_SIZE)

    # 6) Build final records with gating, holding & smoothing
    rows       = []
    last_note  = None
    prev_scale = 0.0
    for idx in range(n_frames):
        t   = round(idx * hop_len / sr, 3)
        amp = rms_vals[idx]

        # gate out noise
        note = freq_to_note(f0_med[idx]) if amp >= gate else None
        if args.hold and note is None:
            note = last_note
        last_note = note

        # brightness smoothing
        raw_scale = amp / max_r
        scale     = prev_scale * args.alpha + raw_scale * (1 - args.alpha)
        prev_scale = scale
        brightness = int(np.clip(scale * 255, 0, 255))

        # color
        if note:
            r,g,b = NOTE_COLORS[note]
        else:
            r,g,b = 0,0,0

        rows.append({
            "frame":      idx,
            "time_sec":   t,
            "brightness": brightness,
            "note":       note or "None",
            "R":          r,
            "G":          g,
            "B":          b
        })

    # 7) Save to CSV
    df = pd.DataFrame(rows)
    df.to_csv(args.output, index=False)
    logging.info("Saved %d frames → %s", len(df), args.output)


if __name__ == "__main__":
    main()
