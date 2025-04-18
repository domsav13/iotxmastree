# real_time_show.py
import time
import threading
import pandas as pd
import pygame

# Import your LED driver—here using the same interface as mapping.py
from mapping import pixels, LED_COUNT

CSV_PATH = "music/really_love_frames.csv"
WAV_PATH = "music/really_love.wav"

def animate_from_csv(csv_path=CSV_PATH, wav_path=WAV_PATH):
    # 1) Load the precomputed frames
    df = pd.read_csv(csv_path)  # columns: time_sec, brightness, R, G, B

    # 2) Initialize audio
    pygame.mixer.init()
    pygame.mixer.music.load(wav_path)
    pygame.mixer.music.play()

    # 3) Frame loop
    start_t = time.perf_counter()
    last_r = last_g = last_b = 0
    for _, row in df.iterrows():
        # Wait until it's time for this frame
        target = row.time_sec
        now    = time.perf_counter() - start_t
        delta  = target - now
        if delta > 0:
            time.sleep(delta)

        # Compute scaled color (RGB → GRB)
        bscale = row.brightness / 255.0
        r = int(row.R * bscale)
        g = int(row.G * bscale)
        b = int(row.B * bscale)
        last_r, last_g, last_b = r, g, b

        # Pack as GRB for the strip
        grb = (g, r, b)
        for i in range(LED_COUNT):
            pixels[i] = grb
        pixels.show()

    # 4) Done—fade out using last color
    for fade in range(50, -1, -1):
        dim = fade / 50.0
        dr = int(last_r * dim)
        dg = int(last_g * dim)
        db = int(last_b * dim)
        grb_fade = (dg, dr, db)
        for i in range(LED_COUNT):
            pixels[i] = grb_fade
        pixels.show()
        time.sleep(0.02)

def start_realtime_show():
    t = threading.Thread(target=animate_from_csv, daemon=True)
    t.start()
    return t
