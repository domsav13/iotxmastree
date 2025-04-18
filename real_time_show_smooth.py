#!/usr/bin/env python3
"""
real_time_show_smooth.py

Live LED show with rate‑limiting, smoothing, and noise‑gating to make the lights clearly follow the music.
"""
import time
import threading
import pandas as pd
import pygame

from mapping import pixels, LED_COUNT

# Configuration
CSV_PATH             = "music/really_love_smoothed.csv"
WAV_PATH             = "music/really_love.wav"
SMOOTH_ALPHA         = 0.3    # brightness smoothing (0–1)
BRIGHTNESS_GATE      = 10     # minimum brightness to accept a new color (0–255)
MIN_UPDATE_INTERVAL  = 0.1    # seconds between LED updates


def animate_from_csv_smooth(csv_path=CSV_PATH, wav_path=WAV_PATH):
    # 1) Load CSV once
    df = pd.read_csv(csv_path)
    frames = df.to_dict('records')

    # 2) Start audio
    pygame.mixer.init()
    pygame.mixer.music.load(wav_path)
    pygame.mixer.music.play()

    # 3) Setup timing
    clock = time.perf_counter
    start_time = clock()

    prev_scale   = 0.0
    last_color   = (0, 0, 0)
    last_up_time = 0.0

    for rec in frames:
        # wait until rec.time_sec
        target = start_time + rec['time_sec']
        now = clock()
        delta = target - now
        if delta > 0:
            time.sleep(delta * 0.8)
            while clock() < target:
                pass

        # rate‑limit updates: skip if too soon
        if rec['time_sec'] - last_up_time < MIN_UPDATE_INTERVAL:
            continue
        last_up_time = rec['time_sec']

        # brightness smoothing
        raw_scale = rec['brightness'] / 255.0
        scale     = prev_scale * SMOOTH_ALPHA + raw_scale * (1 - SMOOTH_ALPHA)
        prev_scale = scale

        # compute candidate RGB
        r = int(rec['R'] * scale)
        g = int(rec['G'] * scale)
        b = int(rec['B'] * scale)

        # noise‑gate: only update when brightness above threshold and valid note
        if rec['note'] != 'None' and rec['brightness'] >= BRIGHTNESS_GATE:
            last_color = (r, g, b)

        # pack as GRB
        grb = (last_color[1], last_color[0], last_color[2])

        # push to LEDs
        for i in range(LED_COUNT):
            pixels[i] = grb
        pixels.show()

    # 4) Fade‑out
    fade_steps = 50
    for step in range(fade_steps, -1, -1):
        f = step / fade_steps
        dr, dg, db = [int(c * f) for c in last_color]
        grb_fade = (dg, dr, db)
        for i in range(LED_COUNT):
            pixels[i] = grb_fade
        pixels.show()
        time.sleep(1.0 / fade_steps)


def start_realtime_show_smooth():
    t = threading.Thread(target=animate_from_csv_smooth, daemon=True)
    t.start()
    return t
