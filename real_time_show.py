import time
import threading
import pandas as pd
import pygame

# Import your LED driver interface
from mapping import pixels, LED_COUNT

# Configuration
CSV_PATH = "music/really_love_smoothed.csv"
WAV_PATH = "music/really_love.wav"
# Runtime smoothing and gating
SMOOTH_ALPHA     = 0.3    # smoothing factor (0 = no smooth, 1 = max smooth)
BRIGHTNESS_GATE  = 10     # minimum brightness to update color (0-255)


def animate_from_csv_smooth(csv_path=CSV_PATH, wav_path=WAV_PATH):
    # Load precomputed, smoothed frames
    df = pd.read_csv(csv_path)
    frames = df.to_dict('records')

    # Initialize audio playback
    pygame.mixer.init()
    pygame.mixer.music.load(wav_path)
    pygame.mixer.music.play()

    # Timing setup
    clock = time.perf_counter
    start_time = clock()

    # State for smoothing and note-holding
    prev_scale = 0.0
    last_color = (0, 0, 0)

    for rec in frames:
        # --- 1) Precise wait ---
        target = start_time + rec['time_sec']
        now = clock()
        delta = target - now
        if delta > 0:
            # Sleep most of the interval
            time.sleep(delta * 0.8)
            # Busy-wait the remainder for high precision
            while clock() < target:
                pass

        # --- 2) Brightness smoothing ---
        raw_scale = rec['brightness'] / 255.0
        scale = prev_scale * SMOOTH_ALPHA + raw_scale * (1 - SMOOTH_ALPHA)
        prev_scale = scale

        # Compute scaled RGB
        r = int(rec['R'] * scale)
        g = int(rec['G'] * scale)
        b = int(rec['B'] * scale)

        # --- 3) Noise gate & note-holding ---
        if rec['note'] != 'None' and rec['brightness'] >= BRIGHTNESS_GATE:
            last_color = (r, g, b)
        grb = (last_color[1], last_color[0], last_color[2])  # pack as GRB

        # --- 4) Update LEDs ---
        for i in range(LED_COUNT):
            pixels[i] = grb
        pixels.show()

    # Fade-out: dim over 1 second
    fade_steps = 50
    for step in range(fade_steps, -1, -1):
        factor = step / fade_steps
        dr = int(last_color[0] * factor)
        dg = int(last_color[1] * factor)
        db = int(last_color[2] * factor)
        grb_fade = (dg, dr, db)
        for i in range(LED_COUNT):
            pixels[i] = grb_fade
        pixels.show()
        time.sleep(1.0 / fade_steps)


def start_realtime_show_smooth():
    t = threading.Thread(target=animate_from_csv_smooth, daemon=True)
    t.start()
    return t
