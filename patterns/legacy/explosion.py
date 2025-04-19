#!/usr/bin/env python3
import os
import time
import random
import math
import pandas as pd
from rpi_ws281x import PixelStrip, Color
import ambient_brightness    # patches PixelStrip.show() to apply ambient dimming

# ─── LED & Coordinate Setup ────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV  = os.path.join(BASE_DIR, 'coordinates.csv')
df          = pd.read_csv(COORDS_CSV)
positions   = df[['X','Y','Z']].values.tolist()
LED_COUNT   = len(positions)

# ─── Strip Configuration ───────────────────────────────────────────────────────
LED_PIN        = 18      # PWM pin connected to the LEDs
LED_FREQ_HZ    = 800000  # LED signal frequency
LED_DMA        = 10      # DMA channel
LED_BRIGHTNESS = 255     # initial brightness (ambient_brightness overrides per show)
LED_INVERT     = False
LED_CHANNEL    = 0

strip = PixelStrip(
    LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
    LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL
)
strip.begin()

def clear_strip():
    """Turn off all LEDs."""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))

# ─── Explosion Effect ─────────────────────────────────────────────────────────
def explosion(center_idx, rings=12, duration=1.2):
    """
    center_idx: LED index to explode from
    rings:      number of concentric rings
    duration:   total time for the effect
    """
    center = positions[center_idx]
    distances = [math.dist(center, pos) for pos in positions]
    max_dist   = max(distances)
    ring_width = max_dist / rings

    for ring in range(rings):
        lower = ring * ring_width
        upper = lower + ring_width
        bri   = int(255 * (1 - ring / (rings - 1)))
        col   = Color(bri, bri, bri)

        clear_strip()
        for i, d in enumerate(distances):
            if lower <= d < upper:
                strip.setPixelColor(i, col)
        strip.show()        # ambient_brightness will adjust actual brightness
        time.sleep(duration / rings)

# ─── Main Loop ────────────────────────────────────────────────────────────────
try:
    while True:
        idx = random.randrange(LED_COUNT)
        explosion(idx, rings=12, duration=1.5)
        time.sleep(0.5)

except KeyboardInterrupt:
    clear_strip()
    strip.show()
