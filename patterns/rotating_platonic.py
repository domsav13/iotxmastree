#!/usr/bin/env python3
"""
rotating_platonic.py

Highlight LEDs approximating a spinning Platonic solid (tetrahedron, cube, icosahedron).
LEDs near the rotated vertices (or edges) light up in shape colors.
"""
import os
import time
import math
import argparse
import pandas as pd
from rpi_ws281x import PixelStrip, Color
import numpy as np
import ambient_brightness

# ─── Platonic Solid Definitions ────────────────────────────────────────────────
# Golden ratio
phi = (1 + math.sqrt(5)) / 2

# Raw vertices before normalization
SOLIDS = {
    'tetra': [
        (1, 1, 1),
        (-1, -1, 1),
        (-1, 1, -1),
        (1, -1, -1)
    ],
    'cube': [
        (x, y, z)
        for x in (-1, 1)
        for y in (-1, 1)
        for z in (-1, 1)
    ],
    'icosa': [
        # (0, ±1, ±phi)
        (0,  s1*1,  s2*phi)
        for s1 in (1, -1)
        for s2 in (1, -1)
    ] + [
        # (±1, ±phi, 0)
        ( s1*1,  s2*phi, 0)
        for s1 in (1, -1)
        for s2 in (1, -1)
    ] + [
        # (±phi, 0, ±1)
        ( s1*phi, 0, s2*1)
        for s1 in (1, -1)
        for s2 in (1, -1)
    ]
}

# Normalize to unit sphere
for name, verts in SOLIDS.items():
    normed = []
    for x, y, z in verts:
        r = math.sqrt(x*x + y*y + z*z)
        normed.append((x/r, y/r, z/r))
    SOLIDS[name] = normed

# ─── Argument Parsing ─────────────────────────────────────────────────────────
parser = argparse.ArgumentParser(description="Rotating Platonic Solid on 3D LED tree")
parser.add_argument("--shape", choices=SOLIDS.keys(), default='tetra',
                    help="Platonic solid to display")
parser.add_argument("--interval", type=float, default=0.05,
                    help="Seconds between frames")
parser.add_argument("--speed", type=float, default=0.1,
                    help="Rotations per second around each axis")
parser.add_argument("--threshold", type=float, default=0.2,
                    help="Distance threshold (fraction of tree radius)")
parser.add_argument("--vertex-color", nargs=3, type=int, default=[255,0,0],
                    metavar=('R','G','B'), help="RGB for vertices")
parser.add_argument("--edge-color", nargs=3, type=int, default=[0,0,255],
                    metavar=('R','G','B'), help="RGB for edges")
parser.add_argument("--show-edges", action="store_true",
                    help="Also highlight edges")
args = parser.parse_args()

SHAPE       = args.shape
INTERVAL    = args.interval
SPEED       = args.speed
THRESH_FRAC = args.threshold
VERTEX_COL  = tuple(args.vertex_color)
EDGE_COL    = tuple(args.edge_color)
SHOW_EDGES  = args.show_edges

# ─── LED & Coordinate Setup ────────────────────────────────────────────────────
BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV = os.path.join(BASE_DIR, 'coordinates.csv')
df         = pd.read_csv(COORDS_CSV)
positions  = df[['X','Y','Z']].values.tolist()
LED_COUNT  = len(positions)

# Compute tree centroid and radius
centroid = [sum(c)/LED_COUNT for c in zip(*positions)]
radius   = max(math.dist(p, centroid) for p in positions)

# Precompute edges if needed
verts = SOLIDS[SHAPE]
edges = []
if SHOW_EDGES:
    for i, v in enumerate(verts):
        # compute distances to others
        dists = [(j, math.dist(v, w)) for j, w in enumerate(verts) if j != i]
        dists.sort(key=lambda x: x[1])
        # connect to 3 nearest neighbors
        for j, _ in dists[:3]:
            if (j, i) not in edges:
                edges.append((i, j))

# Rotation matrix utility
def rotation_matrix(ax, ay, az):
    cx, cy, cz = math.cos(ax), math.cos(ay), math.cos(az)
    sx, sy, sz = math.sin(ax), math.sin(ay), math.sin(az)
    Rx = np.array([[1,0,0],[0, cx,-sx],[0, sx, cx]])
    Ry = np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    Rz = np.array([[cz,-sz,0],[sz, cz,0],[0,0,1]])
    return Rz @ Ry @ Rx

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

# ─── Main Loop ────────────────────────────────────────────────────────────────
t0 = time.perf_counter()
try:
    while True:
        t = time.perf_counter() - t0
        ax = t * SPEED * 2*math.pi
        ay = t * SPEED * 2*math.pi * 0.7
        az = t * SPEED * 2*math.pi * 1.3
        Rm = rotation_matrix(ax, ay, az)

        # rotated vertices
        world_vs = []
        for v in verts:
            rv = Rm @ np.array(v)
            pv = [centroid[i] + rv[i] * radius * 0.8 for i in range(3)]
            world_vs.append(pv)

        clear_strip()
        # highlight vertices
        for pv in world_vs:
            for i, p in enumerate(positions):
                if math.dist(p, pv) <= THRESH_FRAC * radius:
                    strip.setPixelColor(i, Color(*VERTEX_COL))
        # highlight edges
        if SHOW_EDGES:
            for i, j in edges:
                v1 = world_vs[i]
                v2 = world_vs[j]
                for frac in [k/10 for k in range(11)]:
                    pt = [v1[k] * (1-frac) + v2[k] * frac for k in range(3)]
                    for idx, p in enumerate(positions):
                        if math.dist(p, pt) <= THRESH_FRAC * radius:
                            strip.setPixelColor(idx, Color(*EDGE_COL))

        strip.show()
        time.sleep(INTERVAL)

except KeyboardInterrupt:
    clear_strip()
    strip.show()
