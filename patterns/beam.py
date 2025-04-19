#!/usr/bin/env python3
"""
scanning_lightbeam.py

Scanning Lightbeam effect on a 3D LED tree:
Simulates a beam sweeping either horizontally (along Z), diagonally, or radially.
LEDs light up briefly as the beam passes through their coordinate.
"""
import os
import time
import math
import argparse
import pandas as pd
import ambient_brightness    # patches PixelStrip.show() for ambient dimming
from rpi_ws281x import PixelStrip, Color

# ─── Argument Parsing ─────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Scanning Lightbeam effect on 3D LED tree")
parser.add_argument("--mode", choices=["horizontal","diagonal","radial"], default="horizontal",
                    help="Sweep mode: horizontal (Z), diagonal (X+Z), or radial")
parser.add_argument("--interval", type=float, default=0.05,
                    help="Seconds between frames")
parser.add_argument("--speed", type=float, default=1.0,
                    help="Beam travel units (1 unit = full range) per second")
parser.add_argument("--thickness", type=float, default=0.05,
                    help="Beam thickness as fraction of range (0–1)")
parser.add_argument("--color", nargs=3, type=int, default=[255,255,255], metavar=('R','G','B'),
                    help="Beam color RGB")
parser.add_argument("--reverse", action="store_true",
                    help="Reverse sweep direction")
args = parser.parse_args()

MODE       = args.mode
INTERVAL   = args.interval
SPEED      = args.speed
THICK_FRAC = args.thickness
COLOR_RGB  = tuple(args.color)
REVERSE    = -1.0 if args.reverse else 1.0

# ─── LED & Coordinate Setup ────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV  = os.path.join(BASE_DIR, 'coordinates.csv')
df          = pd.read_csv(COORDS_CSV)
positions   = df[['X','Y','Z']].values.tolist()
LED_COUNT   = len(positions)

# Precompute ranges and normalized coords
xs = [p[0] for p in positions]
ys = [p[1] for p in positions]\nzs = [p[2] for p in positions]

x_min, x_max = min(xs), max(xs)
y_min, y_max = min(ys), max(ys)
z_min, z_max = min(zs), max(zs)

# For radial mode, compute centroid XY
a_x = sum(xs)/LED_COUNT
a_y = sum(ys)/LED_COUNT
def radial_coord(p):
    return math.hypot(p[0]-a_x, p[1]-a_y)

# Precompute normalized coordinate based on mode
data_coord = []
if MODE == 'horizontal':
    rng = z_max - z_min
    for x,y,z in positions:
        data_coord.append((z - z_min)/rng if rng>0 else 0.0)
elif MODE == 'diagonal':
    # combine X and Z: use (x_norm + z_norm)/2
    x_rng = x_max - x_min
    z_rng = z_max - z_min
    for x,y,z in positions:
        xn = (x - x_min)/x_rng if x_rng>0 else 0.0
        zn = (z - z_min)/z_rng if z_rng>0 else 0.0
        data_coord.append((xn + zn)/2)
else:  # radial
    # radial distance normalized by max radius
a_max = max(radial_coord(p) for p in positions)
    for p in positions:
        data_coord.append(radial_coord(p)/a_max if a_max>0 else 0.0)

# ─── Strip Configuration ───────────────────────────────────────────────────────
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

# Helper to clear all LEDs
def clear_strip():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))

# Main Loop
start = time.perf_counter()
try:
    while True:
        t = (time.perf_counter() - start) * SPEED * REVERSE
        # beam position cycles from 0 to 1
        pos = (t % 1.0)
        clear_strip()
        # light LEDs within thickness
        for i, frac in enumerate(data_coord):
            if abs(frac - pos) <= THICK_FRAC/2:
                strip.setPixelColor(i, Color(*COLOR_RGB))
        strip.show()
        time.sleep(INTERVAL)

except KeyboardInterrupt:
    clear_strip()
    strip.show()
