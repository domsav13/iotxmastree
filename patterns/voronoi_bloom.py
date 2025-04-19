#!/usr/bin/env python3
"""
voronoi_bloom.py

Voronoi Bloom effect on a 3D LED tree:
Assigns each LED to its nearest random seed and colors it accordingly. Seeds re-randomize periodically with smooth transitions, simulating blooming/crystallization.
"""
import os
import time
import random
import math
import argparse
import pandas as pd
from rpi_ws281x import PixelStrip, Color
import ambient_brightness

# ─── Argument Parsing ─────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="3D Voronoi Bloom on LED tree")
parser.add_argument("-n", "--num-seeds", type=int, default=5,
                    help="Number of Voronoi seed points")
parser.add_argument("-i", "--interval", type=float, default=0.1,
                    help="Seconds between frames")
parser.add_argument("-c", "--change-interval", type=float, default=10.0,
                    help="Seconds between reseeding events")
parser.add_argument("-t", "--transition", type=float, default=2.0,
                    help="Seconds for seed transition interpolation")
args = parser.parse_args()

NUM_SEEDS       = args.num_seeds
FRAME_INTERVAL  = args.interval
CHANGE_INTERVAL = args.change_interval
TRANSITION_TIME = args.transition

# ─── Load LED Coordinates ──────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
COORDS_CPP = os.path.join(BASE_DIR, 'coordinates.csv')
df         = pd.read_csv(COORDS_CPP)
positions  = list(df[['X','Y','Z']].itertuples(index=False, name=None))
LED_COUNT  = len(positions)

# ─── LED Strip Setup ───────────────────────────────────────────────────────────
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
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0,0,0))

# ─── Voronoi Utility ───────────────────────────────────────────────────────────
def choose_seeds():
    idxs = random.sample(range(LED_COUNT), NUM_SEEDS)
    pts = [positions[i] for i in idxs]
    cols = [(
        random.randint(0,255),
        random.randint(0,255),
        random.randint(0,255)
    ) for _ in range(NUM_SEEDS)]
    return pts, cols

# Initialize seeds
t0 = time.time()
last_change = t0
# old and new seeds for transition
o_seeds_pos, o_seeds_col = choose_seeds()
n_seeds_pos, n_seeds_col = o_seeds_pos, o_seeds_col
in_transition = False
trans_start = 0

try:
    while True:
        now = time.time()
        # Trigger reseed
        if now - last_change >= CHANGE_INTERVAL and not in_transition:
            # prepare transition
            o_seeds_pos, o_seeds_col = n_seeds_pos, n_seeds_col
            n_seeds_pos, n_seeds_col = choose_seeds()
            trans_start = now
            in_transition = True
            last_change = now

        # Compute interpolation factor
        if in_transition:
            f = (now - trans_start) / TRANSITION_TIME
            if f >= 1.0:
                f = 1.0
                in_transition = False
            # interpolate seed positions and colors
            seeds_pos = []
            seeds_col = []
            for (ox,oy,oz), (nx,ny,nz), oc, nc in zip(o_seeds_pos, n_seeds_pos, o_seeds_col, n_seeds_col):
                seeds_pos.append((ox + (nx-ox)*f,
                                  oy + (ny-oy)*f,
                                  oz + (nz-oz)*f))
                seeds_col.append((
                    int(oc[0] + (nc[0]-oc[0])*f),
                    int(oc[1] + (nc[1]-oc[1])*f),
                    int(oc[2] + (nc[2]-oc[2])*f)
                ))
        else:
            seeds_pos = n_seeds_pos
            seeds_col = n_seeds_col

        # Assign each LED to nearest seed
        clear_strip()
        for i, p in enumerate(positions):
            # find nearest
            best_j = 0
            best_d = math.dist(p, seeds_pos[0])
            for j in range(1, NUM_SEEDS):
                d = math.dist(p, seeds_pos[j])
                if d < best_d:
                    best_d = d
                    best_j = j
            r,g,b = seeds_col[best_j]
            strip.setPixelColor(i, Color(r, g, b))

        strip.show()
        time.sleep(FRAME_INTERVAL)

except KeyboardInterrupt:
    clear_strip()
    strip.show()
