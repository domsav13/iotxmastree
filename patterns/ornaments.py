#!/usr/bin/env python3
"""
ornament_drop.py

Animate ornaments "falling" onto a 3D LED tree, bouncing and then twinkling when settled.
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
parser = argparse.ArgumentParser(description="Ornament Drop effect on 3D LED tree")
parser.add_argument("-n", "--num-ornaments", type=int, default=5,
                    help="Number of concurrent ornaments")
parser.add_argument("-i", "--interval", type=float, default=0.05,
                    help="Seconds between animation frames")
parser.add_argument("-s", "--speed", type=float, default=5.0,
                    help="Fall speed (units per second)")
parser.add_argument("--hold-time", type=float, default=2.0,
                    help="Seconds to hold twinkle before respawn")
parser.add_argument("--bounce-damp", type=float, default=0.5,
                    help="Damping factor for bounce height")
parser.add_argument("--init-offset", type=float, default=0.2,
                    help="Spawn Z offset as fraction of tree height")
args = parser.parse_args()

NUM_ORNAMENTS = args.num_ornaments
INTERVAL      = args.interval
SPEED         = args.speed
HOLD_TIME     = args.hold_time
BOUNCE_DAMP   = args.bounce_damp
INIT_OFFSET   = args.init_offset

# ─── LED & Coordinate Setup ────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV  = os.path.join(BASE_DIR, 'coordinates.csv')
df          = pd.read_csv(COORDS_CSV)
positions   = df[['X','Y','Z']].values.tolist()
LED_COUNT   = len(positions)

# find tree z bounds
tree_zs    = [pos[2] for pos in positions]
tree_z_min = min(tree_zs)
tree_z_max = max(tree_zs)
tree_height = tree_z_max - tree_z_min

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

def clear_strip():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))

# possible ornament colors (r, g, b)
ORNAMENT_COLORS = [
    (0, 255, 0),    # red
    (215, 255, 0),  # gold
    (0, 0, 255),    # blue
]

# helper to spawn a new ornament
def new_ornament():
    x = random.uniform(min(p[0] for p in positions), max(p[0] for p in positions))
    y = random.uniform(min(p[1] for p in positions), max(p[1] for p in positions))
    z = tree_z_max + INIT_OFFSET * tree_height
    color = random.choice(ORNAMENT_COLORS)
    return {
        'x': x, 'y': y, 'current_z': z,
        'state': 'falling', 'bounce_h': INIT_OFFSET * tree_height,
        'color': color,
        'tw_f': random.uniform(1.0, 3.0),
        'phase': random.uniform(0, 2*math.pi),
        'land_time': None,
        'landed_idx': None,
    }

# initialize ornaments
ornaments = [new_ornament() for _ in range(NUM_ORNAMENTS)]

# main animation loop
prev_time = time.time()
while True:
    now = time.time()
    dt = now - prev_time
    prev_time = now

    # update ornament physics
    for o in ornaments:
        if o['state'] == 'falling':
            o['current_z'] -= SPEED * dt
            if o['current_z'] <= tree_z_min:
                o['state'] = 'bounce'
                o['bounce_h'] = INIT_OFFSET * tree_height
        elif o['state'] == 'bounce':
            o['bounce_h'] *= BOUNCE_DAMP
            o['current_z'] = tree_z_min + o['bounce_h']
            if o['bounce_h'] < 0.01 * tree_height:
                # landed
                o['state'] = 'landed'
                o['current_z'] = tree_z_min
                # find closest LED index to land point
                min_i = min(range(LED_COUNT),
                    key=lambda i: (
                        (positions[i][0]-o['x'])**2 +
                        (positions[i][1]-o['y'])**2 +
                        (positions[i][2]-o['current_z'])**2
                    )
                )
                o['landed_idx'] = min_i
                o['land_time'] = now
        elif o['state'] == 'landed':
            if now - o['land_time'] >= HOLD_TIME:
                # respawn
                o.update(new_ornament())

    # draw frame
    clear_strip()
    for o in ornaments:
        if o['state'] in ('falling', 'bounce'):
            # map current position to nearest LED
            idx = min(range(LED_COUNT),
                key=lambda i: (
                    (positions[i][0]-o['x'])**2 +
                    (positions[i][1]-o['y'])**2 +
                    (positions[i][2]-o['current_z'])**2
                )
            )
            strip.setPixelColor(idx, Color(*o['color']))
        else:  # landed => twinkle
            t = now - o['land_time']
            f = 0.5 + 0.5 * math.sin(2*math.pi*o['tw_f']*t + o['phase'])
            r = int(o['color'][0] * f)
            g = int(o['color'][1] * f)
            b = int(o['color'][2] * f)
            strip.setPixelColor(o['landed_idx'], Color(r, g, b))

    strip.show()
    time.sleep(INTERVAL)
