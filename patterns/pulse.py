#!/usr/bin/env python3
"""
galaxy_core_pulse.py

Galaxy Core Pulse effect on a 3D LED tree:
Expanding radial ripples from a central LED, fading outward.
"""
import os
import time
import math
import argparse
import pandas as pd
from rpi_ws281x import PixelStrip, Color
import ambient_brightness

# ─── Argument Parsing ─────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Galaxy Core Pulse effect on 3D LED tree")
parser.add_argument("--center", type=int, default=None,
                    help="Index of central LED (default: nearest to tree centroid)")
parser.add_argument("--interval", type=float, default=0.05,
                    help="Seconds between frames")
parser.add_argument("--speed", type=float, default=10.0,
                    help="Expansion speed (units per second)")
parser.add_argument("--thickness", type=float, default=0.1,
                    help="Pulse thickness as fraction of max distance (0-1)")
parser.add_argument("--color", nargs=3, type=int, default=[255,255,255],
                    metavar=('R','G','B'), help="Base RGB color for the pulse")
args = parser.parse_args()

# ─── LED & Coordinate Setup ────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV = os.path.join(BASE_DIR, 'coordinates.csv')
df         = pd.read_csv(COORDS_CSV)
positions  = df[['X','Y','Z']].values.tolist()
LED_COUNT  = len(positions)

# Determine tree centroid and choose center LED
if args.center is None:
    centroid = [sum(c)/LED_COUNT for c in zip(*positions)]
    center_idx = min(range(LED_COUNT), key=lambda i: math.dist(positions[i], centroid))
else:
    center_idx = args.center
center_pos = positions[center_idx]

# Compute distances from center
distances = [math.dist(center_pos, pos) for pos in positions]
max_dist = max(distances)
thickness = args.thickness * max_dist

# Strip config
LED_PIN        = 18
LED_FREQ_HZ    = 800000
LED_DMA        = 10
LED_BRIGHTNESS = 255
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
        strip.setPixelColor(i, Color(0,0,0))

# Base color
base_r, base_g, base_b = args.color

# Main animation loop
start_time = time.perf_counter()
try:
    while True:
        t = time.perf_counter() - start_time
        radius = (t * args.speed) % (max_dist + thickness)

        # Update LEDs
        for i, d in enumerate(distances):
            diff = abs(d - radius)
            if diff <= thickness:
                factor = 1 - (diff / thickness)
                r = int(base_r * factor)
                g = int(base_g * factor)
                b = int(base_b * factor)
            else:
                r = g = b = 0
            strip.setPixelColor(i, Color(r, g, b))

        strip.show()
        time.sleep(args.interval)

except KeyboardInterrupt:
    clear_strip()
    strip.show()
