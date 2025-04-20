"""
Compass Rose / Angular Starburst effect on a 3D LED tree:
Lights up LEDs in rotating angular slices (like a compass needle or starburst).
"""
import os
import time
import math
import argparse
import pandas as pd
from rpi_ws281x import PixelStrip, Color
import ambient_brightness

parser = argparse.ArgumentParser(description="Compass Rose angular starburst on 3D LED tree")
parser.add_argument("-n", "--num-slices", type=int, default=8,
                    help="Total angular slices around 360°")
parser.add_argument("-w", "--width", type=int, default=1,
                    help="Number of adjacent slices lit at once")
parser.add_argument("-r", "--rps", type=float, default=0.2,
                    help="Rotations per second of the beam")
parser.add_argument("-i", "--interval", type=float, default=0.05,
                    help="Seconds between frames")
parser.add_argument("--color", nargs=3, type=int, default=[255,255,255], metavar=('R','G','B'),
                    help="Beam color RGB")
parser.add_argument("--reverse", action="store_true",
                    help="Rotate in reverse direction")
args = parser.parse_args()

NUM_SLICES = args.num_slices
WIDTH      = max(1, min(NUM_SLICES, args.width))
RPS        = args.rps
INTERVAL   = args.interval
COLOR      = tuple(args.color)
REVERSE    = -1.0 if args.reverse else 1.0

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV = os.path.join(BASE_DIR, 'coordinates.csv')
df         = pd.read_csv(COORDS_CSV)
positions  = df[['X','Y','Z']].values.tolist()
LED_COUNT  = len(positions)

xs = [p[0] for p in positions]
ys = [p[1] for p in positions]
cx = sum(xs) / LED_COUNT
cy = sum(ys) / LED_COUNT

led_frac = []
for x, y, _ in positions:
    theta = math.atan2(y - cy, x - cx)  # -pi..pi
    frac  = (theta / (2 * math.pi) + 1.0) % 1.0  # normalize to [0,1)
    led_frac.append(frac)

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
        t = (time.perf_counter() - start)
        pos = (t * RPS * REVERSE) % 1.0
        current_slice = int(pos * NUM_SLICES)
        active = {(current_slice + offset) % NUM_SLICES for offset in range(WIDTH)}

        clear_strip()
        for i, frac in enumerate(led_frac):
            slice_idx = int(frac * NUM_SLICES)
            if slice_idx in active:
                strip.setPixelColor(i, Color(*COLOR))
        strip.show()
        time.sleep(INTERVAL)

except KeyboardInterrupt:
    clear_strip()
    strip.show()
