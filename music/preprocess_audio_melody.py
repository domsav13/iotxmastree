#!/usr/bin/env python3
"""
preprocess_audio_melody.py

Extracts frame‑level brightness & note color CSV for the song's main melody only.
Uses harmonic‑percussive source separation to isolate melodic content.
"""
import os
import sys
import argparse
import logging
import math

import numpy as np
import pandas as pd
import librosa
from aubio import source, pitch as AubioPitch

# Defaults
DEFAULT_INPUT       = "really_love.wav"
DEFAULT_OUTPUT      = "really_love_melody.csv"
DEFAULT_SR          = 8000    # downsample rate
DEFAULT_FRAME_SEC   = 0.04    # 40 ms
DEFAULT_OVERLAP     = 0.5     # 50% overlap
DEFAULT_RMS_THRESH  = 0.05    # gate threshold
DEFAULT_HOLD        = True   # hold last note
DEFAULT_ALPHA       = 0.3    # smoothing

NOTE_COLORS = {
  'C': (255,0,0), 'D': (255,128,0), 'E': (255,255,0),
  'F': (0,255,0), 'G': (0,255,255), 'A': (0,0,255),
  'B': (128,0,255),
}

def freq_to_note(freq):
    if freq <= 0 or math.isnan(freq): return None
    nm = librosa.hz_to_note(freq, octave=False)
    return nm[0] if nm[0] in NOTE_COLORS else None

def parse_args():
    p = argparse.ArgumentParser()
    p.add_argument('-i','--input',       default=DEFAULT_INPUT, help='Input WAV')
    p.add_argument('-o','--output',      default=DEFAULT_OUTPUT, help='Output CSV')
    p.add_argument('--sr', type=int,     default=DEFAULT_SR, help='Resample Hz')
    p.add_argument('-f','--frame_duration', type=float, default=DEFAULT_FRAME_SEC, help='Frame length s')
    p.add_argument('-l','--overlap',     type=float, default=DEFAULT_OVERLAP, help='Overlap frac')
    p.add_argument('-t','--rms_threshold', type=float, default=DEFAULT_RMS_THRESH, help='Gate RMS frac')
    p.add_argument('--hold', action='store_true', default=DEFAULT_HOLD, help='Hold last note')
    p.add_argument('--alpha', type=float, default=DEFAULT_ALPHA, help='Brightness smoothing')
    return p.parse_args()

def main():
    args = parse_args()
    logging.basicConfig(level=logging.INFO, format='%(asctime)s %(levelname)s: %(message)s')

    if not os.path.isfile(args.input):
        logging.error('Missing WAV: %s', args.input)
        sys.exit(1)

    # load and separate
    logging.info('Loading %s at %d Hz', args.input, args.sr)
    y, sr = librosa.load(args.input, sr=args.sr)
    y_harm, y_perc = librosa.effects.hpss(y)

    frame_len = int(args.frame_duration * sr)
    hop_len = max(1, int(frame_len * (1-args.overlap)))
    n_frames = 1 + max(0, (len(y_harm) - frame_len)//hop_len)
    logging.info('Frames: %d (frame_len=%d, hop_len=%d)', n_frames, frame_len, hop_len)

    # rms on harmonic only
    rms_vals = np.empty(n_frames)
    for i in range(n_frames):
        w = y_harm[i*hop_len: i*hop_len + frame_len]
        if len(w) < frame_len: w = np.pad(w, (0, frame_len - len(w)))
        rms_vals[i] = math.sqrt(np.mean(w*w))
    max_r = rms_vals.max()
    gate = max_r * args.rms_threshold
    logging.info('Max RMS=%.6f, gate=%.6f', max_r, gate)

    # aubio pitch on harmonic
    src = source(args.input, samplerate=sr, hop_size=hop_len)
    pitch_o = AubioPitch('yin', frame_len, hop_len, sr)
    pitch_o.set_unit('Hz'); pitch_o.set_silence(-40)

    f0_vals = []
    while True:
        s, read = src()
        if read < hop_len: break
        # separate this block
        h_block, _ = librosa.effects.hpss(s[:frame_len])
        f0_vals.append(pitch_o(h_block)[0])
    f0_vals = (f0_vals + [0]*n_frames)[:n_frames]

    # assemble
    rows=[]
    last_note=None; prev_scale=0.0
    for i in range(n_frames):
        t = round(i*hop_len/sr,3)
        amp = rms_vals[i]
        note = freq_to_note(f0_vals[i]) if amp>=gate else None
        if args.hold and note is None: note=last_note
        last_note=note
        raw = amp/max_r
        scale = prev_scale*args.alpha + raw*(1-args.alpha)
        prev_scale=scale
        bright=int(np.clip(scale*255,0,255))
        if note: r,g,b=NOTE_COLORS[note]
        else: r,g,b=0,0,0
        rows.append({'frame':i,'time_sec':t,'brightness':bright,'note':note or 'None','R':r,'G':g,'B':b})

    df=pd.DataFrame(rows)
    df.to_csv(args.output,index=False)
    logging.info('Saved %d frames → %s',len(df),args.output)

if __name__=='__main__':
    main()
