"""
Double Helix DNA Twist effect on a 3D LED tree:
Two intertwining color bands spiral up/down the tree.
"""
import os
import time
import math
import argparse
import pandas as pd
from rpi_ws281x import PixelStrip, Color
import ambient_brightness

parser = argparse.ArgumentParser(description="Double Helix DNA Twist on 3D LED tree")
parser.add_argument("--interval", type=float, default=0.05,
                    help="Seconds between frames")
parser.add_argument("--rps", type=float, default=0.2,
                    help="Rotations per second around the tree")
parser.add_argument("--turns", type=float, default=3.0,
                    help="Number of helix turns from bottom to top")
parser.add_argument("--color1", nargs=3, type=int, default=[255,0,0], metavar=('R','G','B'),
                    help="RGB color for strand 1 (default red)")
parser.add_argument("--color2", nargs=3, type=int, default=[0,0,255], metavar=('R','G','B'),
                    help="RGB color for strand 2 (default blue)")
parser.add_argument("--reverse", action="store_true",
                    help="Reverse vertical direction")
parser.add_argument("--range", type=float, default=1.0,
                    help="Fraction of tree height to animate (0–1)")
args = parser.parse_args()

INTERVAL = args.interval
RPS      = args.rps
TURNS    = args.turns
COLOR1   = tuple(args.color1)
COLOR2   = tuple(args.color2)
REVERSE  = -1.0 if args.reverse else 1.0
Z_RANGE  = max(0.0, min(1.0, args.range))

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV = os.path.join(BASE_DIR, 'coordinates.csv')
df         = pd.read_csv(COORDS_CSV)
positions  = df[['X','Y','Z']].values.tolist()
LED_COUNT  = len(positions)

zs = [p[2] for p in positions]
z_min, z_max = min(zs), max(zs)
height = z_max - z_min if z_max>z_min else 1.0

led_theta = []
led_znorm = []
for x, y, z in positions:
    theta = math.atan2(y, x)  # -π..π
    z_norm = (z - z_min) / height
    z_norm = z_norm * Z_RANGE
    led_theta.append(theta)
    led_znorm.append(z_norm)

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
        strip.setPixelColor(i, Color(0, 0, 0))

start = time.perf_counter()
try:
    while True:
        t = (time.perf_counter() - start) * RPS * 2 * math.pi * REVERSE
        clear_strip()
        for i in range(LED_COUNT):
            theta = led_theta[i]
            zf    = led_znorm[i]
            phase = theta + t + 2 * math.pi * TURNS * (1 - zf)
            v1 = max(0.0, math.sin(phase))
            v2 = max(0.0, math.sin(phase + math.pi))
            r = int(COLOR1[0] * v1 + COLOR2[0] * v2)
            g = int(COLOR1[1] * v1 + COLOR2[1] * v2)
            b = int(COLOR1[2] * v1 + COLOR2[2] * v2)
            strip.setPixelColor(i, Color(r, g, b))
        strip.show()
        time.sleep(INTERVAL)

except KeyboardInterrupt:
    clear_strip()
    strip.show()
