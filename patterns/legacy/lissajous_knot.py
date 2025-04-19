#!/usr/bin/env python3
"""
lissajous_knot.py

3D Lissajous Knot animation on a 3D LED tree:
Traces a parametric knot path; nearest LED to the moving point lights up each frame,
leaving a fading trail.
"""
import os
import time
import math
import argparse
import pandas as pd
import ambient_brightness    # patches PixelStrip.show() for ambient dimming
from rpi_ws281x import PixelStrip, Color

# ─── Argument Parsing ─────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="3D Lissajous Knot on LED tree")
parser.add_argument("--a", type=float, default=3.0, help="frequency a for x(t)")
parser.add_argument("--b", type=float, default=2.0, help="frequency b for y(t)")
parser.add_argument("--c", type=float, default=5.0, help="frequency c for z(t)")
parser.add_argument("--delta", type=float, default=math.pi/2,
                    help="phase offset δ for x(t)")
parser.add_argument("--interval", type=float, default=0.02,
                    help="Seconds between frames")
parser.add_argument("--fade", type=float, default=0.9,
                    help="Fade factor per frame (0-1) for trail")
parser.add_argument("--color", nargs=3, type=int, default=[255,255,255], metavar=('R','G','B'),
                    help="Trail color RGB")
args = parser.parse_args()

# Unpack parameters
a, b, c = args.a, args.b, args.c
delta     = args.delta
INTERVAL  = args.interval
FADE      = max(0.0, min(1.0, args.fade))
COL       = tuple(args.color)

# ─── Load LED coordinates ─────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV = os.path.join(BASE_DIR, 'coordinates.csv')
df         = pd.read_csv(COORDS_CSV)
positions  = df[['X','Y','Z']].values.tolist()
LED_COUNT  = len(positions)

# Determine spatial bounds to map parametric [-1,1] to tree extents
xs = [p[0] for p in positions]
ys = [p[1] for p in positions]
zs = [p[2] for p in positions]
x_min, x_max = min(xs), max(xs)
y_min, y_max = min(ys), max(ys)
z_min, z_max = min(zs), max(zs)

# Setup LED strip
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

# Initialize trail intensity buffer
trail = [0.0] * LED_COUNT

# Map normalized parametric point to tree coords
def map_to_tree(xn, yn, zn):
    x = x_min + (xn + 1) * 0.5 * (x_max - x_min)
    y = y_min + (yn + 1) * 0.5 * (y_max - y_min)
    z = z_min + (zn + 1) * 0.5 * (z_max - z_min)
    return (x, y, z)

# Utility to clear strip
def clear_strip():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0,0,0))

# Main loop
start = time.perf_counter()
try:
    while True:
        t = time.perf_counter() - start
        # Parametric Lissajous coordinates
        xn = math.sin(a * t + delta)
        yn = math.sin(b * t)
        zn = math.sin(c * t)
        # Map to real coords
        px, py, pz = map_to_tree(xn, yn, zn)
        # Find nearest LED
        best_idx = min(range(LED_COUNT),
                       key=lambda i: (positions[i][0]-px)**2 +
                                     (positions[i][1]-py)**2 +
                                     (positions[i][2]-pz)**2)
        # Fade trail
        for i in range(LED_COUNT):
            trail[i] *= FADE
        # Light current point at full intensity
        trail[best_idx] = 1.0
        # Render
        for i, intensity in enumerate(trail):
            val = int(max(0.0, min(1.0, intensity)) * 255)
            r = int(COL[0] * (val/255.0))
            g = int(COL[1] * (val/255.0))
            b = int(COL[2] * (val/255.0))
            strip.setPixelColor(i, Color(r, g, b))
        strip.show()
        time.sleep(INTERVAL)

except KeyboardInterrupt:
    clear_strip()
    strip.show()
