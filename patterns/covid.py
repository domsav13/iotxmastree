#!/usr/bin/env python3
import time
import random
import math
import pandas as pd
import ambient_brightness    # patches PixelStrip.show() for ambient dimming
from rpi_ws281x import PixelStrip, Color

# ─── LED & Coordinate Setup ────────────────────────────────────────────────────
BASE_DIR   = __import__('os').path.dirname(__import__('os').path.abspath(__file__))
COORDS_CSV = __import__('os').path.join(BASE_DIR, 'coordinates.csv')
df         = pd.read_csv(COORDS_CSV)
df['led_index'] = df.index
LED_COUNT  = len(df)

# ─── Strip Configuration ───────────────────────────────────────────────────────
LED_PIN        = 18
LED_FREQ_HZ    = 800000
LED_DMA        = 10
LED_BRIGHTNESS = 125
LED_INVERT     = False
LED_CHANNEL    = 0

strip = PixelStrip(
    LED_COUNT, LED_PIN, LED_FREQ_HZ,
    LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL
)
strip.begin()

def clear_strip():
    """Turn off all LEDs."""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))

# Precompute LED coordinates list for fast access
led_coords = [(row['X'], row['Y'], row['Z']) for _, row in df.iterrows()]

def animate_contagious_effect(interval=0.01, contagion_speed=1.0, hold_time=0.5):
    """
    Loop forever: pick a random LED & color, then spread it outward over the tree.
    interval:    seconds between frames
    contagion_speed: units per second spread rate
    hold_time:   seconds to hold full tree lit before restart
    """
    while True:
        # Choose random start LED and random GRB color
        start_idx = random.randrange(LED_COUNT)
        sx, sy, sz = led_coords[start_idx]
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        contagion_color = Color(r, g, b)

        # Compute distances from start to every LED
        distances = []
        max_dist = 0.0
        for (x, y, z) in led_coords:
            d = math.dist((sx, sy, sz), (x, y, z))
            distances.append(d)
            if d > max_dist:
                max_dist = d

        # How long to spread across full tree
        spread_duration = max_dist / contagion_speed if contagion_speed > 0 else 0

        # Animate spread
        t0 = time.time()
        while True:
            elapsed = time.time() - t0
            radius  = contagion_speed * elapsed
            clear_strip()
            for idx, d in enumerate(distances):
                if d <= radius:
                    strip.setPixelColor(idx, contagion_color)
            strip.show()
            if elapsed >= spread_duration:
                break
            time.sleep(interval)

        # Hold full tree lit
        for i in range(LED_COUNT):
            strip.setPixelColor(i, contagion_color)
        strip.show()
        time.sleep(hold_time)

        # Reset (already cleared on next loop start)
        clear_strip()
        strip.show()
        time.sleep(interval)

if __name__ == '__main__':
    # Run indefinitely
    animate_contagious_effect(
        interval=0.01,
        contagion_speed=8.5,
        hold_time=0.5
    )
