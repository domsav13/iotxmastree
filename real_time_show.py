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
    df = pd.read_csv(csv_path)  # expects columns: time_sec, brightness, R, G, B
    # 2) Initialize audio
    pygame.mixer.init()
    pygame.mixer.music.load(wav_path)
    pygame.mixer.music.play()
    # 3) Frame loop
    start_t = time.perf_counter()
    for _, row in df.iterrows():
        # Wait until it's time for this frame
        target = row.time_sec
        now    = time.perf_counter() - start_t
        delta  = target - now
        if delta > 0:
            time.sleep(delta)
        # Compute scaled color
        bscale = row.brightness / 255.0
        r = int(row.R * bscale)
        g = int(row.G * bscale)
        b = int(row.B * bscale)
        # Push to every LED
        for i in range(LED_COUNT):
            pixels[i] = (r, g, b)
        pixels.show()
    # 4) Done—fade out
    for fade in range(50, -1, -1):
        dim = fade / 50.0
        for i in range(LED_COUNT):
            pixels[i] = (int(r * dim), int(g * dim), int(b * dim))
        pixels.show()
        time.sleep(0.02)

def start_realtime_show():
    t = threading.Thread(target=animate_from_csv, daemon=True)
    t.start()
    return t
