# real_time_show.py

import time
import threading
import pandas as pd
import pygame
import ambient_brightness
from mapping import pixels, LED_COUNT

CSV_PATH = "music/really_love_frames.csv"
WAV_PATH = "music/really_love.wav"

def animate_from_csv(csv_path=CSV_PATH, wav_path=WAV_PATH):
    # 1) Load precomputed frames
    df = pd.read_csv(csv_path)  # columns: time_sec, brightness, R, G, B

    # 2) Initialize and play audio
    pygame.mixer.init()
    pygame.mixer.music.load(wav_path)
    pygame.mixer.music.play()

    # 3) Iterate frames in real time
    start_t = time.perf_counter()
    last_r = last_g = last_b = 0
    for _, row in df.iterrows():
        target = row.time_sec
        now    = time.perf_counter() - start_t
        delta  = target - now
        if delta > 0:
            time.sleep(delta)

        # scale RGB by brightness, then pack as GRB for NeoPixel
        bscale = row.brightness / 255.0
        r = int(row.R * bscale)
        g = int(row.G * bscale)
        b = int(row.B * bscale)
        last_r, last_g, last_b = r, g, b

        grb = (g, r, b)
        for i in range(LED_COUNT):
            pixels[i] = grb
        pixels.show()

    # 4) Fade out
    for fade in range(50, -1, -1):
        dim     = fade / 50.0
        dr, dg, db = (int(last_r * dim),
                      int(last_g * dim),
                      int(last_b * dim))
        grb_fade = (dg, dr, db)
        for i in range(LED_COUNT):
            pixels[i] = grb_fade
        pixels.show()
        time.sleep(0.02)

def start_realtime_show():
    t = threading.Thread(target=animate_from_csv, daemon=True)
    t.start()
    return t
