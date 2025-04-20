import os
import time
import random
import math
import argparse
import pandas as pd
from rpi_ws281x import PixelStrip, Color
import ambient_brightness

parser = argparse.ArgumentParser(description="Multi‑snake effect on 3D LED tree")
parser.add_argument("-n", "--num-snakes", type=int, default=1,
                    help="Number of independent snakes")
parser.add_argument("-l", "--length", type=int, default=15,
                    help="Length of each snake in LEDs")
parser.add_argument("-d", "--delay", type=float, default=0.1,
                    help="Seconds between frames (frame rate) ")
parser.add_argument("-k", "--neighbors", type=int, default=6,
                    help="Number of nearest neighbors for movement")
parser.add_argument("--min-bright", type=int, default=50,
                    help="Minimum segment brightness")
parser.add_argument("--max-bright", type=int, default=255,
                    help="Maximum segment brightness")
args = parser.parse_args()

NUM_SNAKES    = args.num_snakes
SNAKE_LENGTH  = args.length
FRAME_DELAY   = args.delay
NEIGHBORS_K   = args.neighbors
MIN_SEG_BRIGHT = args.min_bright
MAX_SEG_BRIGHT = args.max_bright

BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV  = os.path.join(BASE_DIR, 'coordinates.csv')
df          = pd.read_csv(COORDS_CSV)
positions   = df[['X','Y','Z']].values.tolist()
LED_COUNT   = len(positions)

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

dist_matrix = []
for i, p in enumerate(positions):
    dists = [(j, math.dist(p, q)) for j, q in enumerate(positions) if j != i]
    dists.sort(key=lambda x: x[1])
    dist_matrix.append([idx for idx, _ in dists[:NEIGHBORS_K]])

snakes = []
colors = []
for _ in range(NUM_SNAKES):
    snakes.append([random.randrange(LED_COUNT)])
    colors.append((
        random.randint(0, 255),
        random.randint(0, 255),
        random.randint(0, 255),
    ))

def choose_next(head, body):
    neighs  = dist_matrix[head]
    choices = [n for n in neighs if n not in body]
    return random.choice(choices) if choices else random.choice(neighs)

try:
    while True:
        for s in snakes:
            head = s[-1]
            nxt  = choose_next(head, s)
            s.append(nxt)
            if len(s) > SNAKE_LENGTH:
                s.pop(0)

        clear_strip()
        for s_idx, s in enumerate(snakes):
            base_r, base_g, base_b = colors[s_idx]
            for seg_idx, led in enumerate(s):
                frac = seg_idx / (SNAKE_LENGTH - 1)
                bri  = MIN_SEG_BRIGHT + frac * (MAX_SEG_BRIGHT - MIN_SEG_BRIGHT)
                scale = bri / 255.0
                r = int(base_r * scale)
                g = int(base_g * scale)
                b = int(base_b * scale)
                strip.setPixelColor(led, Color(r, g, b))
        strip.show()

        time.sleep(FRAME_DELAY)

except KeyboardInterrupt:
    clear_strip()
    strip.show()
