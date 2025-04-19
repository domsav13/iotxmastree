#!/usr/bin/env python3
"""
icicle_growth.py

Simulate icicles forming from top to bottom on a 3D LED tree, with shimmer and melting.
"""
import os
import time
import random
import math
import argparse
import pandas as pd
import ambient_brightness    # patches PixelStrip.show() for ambient dimming
from rpi_ws281x import PixelStrip, Color

# ─── Argument Parsing ─────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Icicle Growth effect on 3D LED tree")
parser.add_argument("-n", "--num-icicles", type=int, default=5,
                    help="Number of icicles to grow")
parser.add_argument("--interval", type=float, default=0.05,
                    help="Delay between frames in seconds")
parser.add_argument("--grow-speed", type=float, default=5.0,
                    help="LEDs grown per second per icicle")
parser.add_argument("--shimmer", type=float, default=0.1,
                    help="Probability (0-1) to shimmer each lit LED per frame")
parser.add_argument("--hold-time", type=float, default=2.0,
                    help="Seconds to hold full icicles before melting")
args = parser.parse_args()

NUM_ICICLES = args.num_icicles
INTERVAL    = args.interval
GROW_SPEED  = args.grow_speed
SHIMMER_P   = args.shimmer
HOLD_TIME   = args.hold_time

# ─── LED & Coordinate Setup ────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV  = os.path.join(BASE_DIR, 'coordinates.csv')
df          = pd.read_csv(COORDS_CSV)
positions   = df[['X','Y','Z']].values.tolist()
LED_COUNT   = len(positions)

# determine Z bounds for top selection
tree_zs    = [pos[2] for pos in positions]
tree_z_min = min(tree_zs)
tree_z_max = max(tree_zs)
# indices of top-tier LEDs (within top 10% of height)
top_threshold = tree_z_max - 0.1*(tree_z_max - tree_z_min)
seed_indices = [i for i,z in enumerate(tree_zs) if z >= top_threshold]

# Precompute lower-neighbor mapping: for each LED, nearest neighbor with lower Z
children = {}
for i, (x,y,z) in enumerate(positions):
    # find all candidates below
    cand = [(j, math.dist((x,y,z), positions[j]))
            for j,(x2,y2,z2) in enumerate(positions) if z2 < z]
    if cand:
        # pick closest
        j,_ = min(cand, key=lambda t:t[1])
        children[i] = j

# build icicle paths
paths = []
for _ in range(NUM_ICICLES):
    start = random.choice(seed_indices)
    path = [start]
    while path[-1] in children:
        nxt = children[path[-1]]
        # avoid cycles
        if nxt in path:
            break
        path.append(nxt)
    paths.append(path)

# ─── Strip Setup ───────────────────────────────────────────────────────────────
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

# helper to clear all
def clear_strip():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))

# map position in path to icy color gradient
def icy_color(idx, length):
    frac = idx / max(1, length-1)
    # tip is white, base is blue
    r = int(255*(1-frac))
    g = int(255*(1-frac))
    b = 255
    return (r, g, b)

# ─── Animation Loop ───────────────────────────────────────────────────────────
while True:
    # growth phase
    max_len = max(len(p) for p in paths)
    # total grow time per icicle
    total_time = max_len / GROW_SPEED
    t0 = time.time()
    while True:
        elapsed = time.time() - t0
        frac = min(1.0, elapsed / total_time)
        # current growth index
        cur_n = int(frac * max_len)
        clear_strip()
        # draw each path
        for path in paths:
            for i, led in enumerate(path[:cur_n]):
                r,g,b = icy_color(i, len(path))
                # shimmer
                if random.random() < SHIMMER_P:
                    scale = random.uniform(0.5,1.0)
                    r,g,b = int(r*scale), int(g*scale), int(b*scale)
                strip.setPixelColor(led, Color(r, g, b))
        strip.show()
        time.sleep(INTERVAL)
        if elapsed >= total_time:
            break
    # hold full icicles
    time.sleep(HOLD_TIME)
    # melting phase (reverse growth)
    t0 = time.time()
    while True:
        elapsed = time.time() - t0
        frac = min(1.0, elapsed / total_time)
        cur_n = max_len - int(frac * max_len)
        clear_strip()
        for path in paths:
            for i, led in enumerate(path[:cur_n]):
                r,g,b = icy_color(i, len(path))
                strip.setPixelColor(led, Color(r, g, b))
        strip.show()
        time.sleep(INTERVAL)
        if elapsed >= total_time:
            break
    # short pause before next cycle
    time.sleep(1.0)
