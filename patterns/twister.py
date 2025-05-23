"""
Helical vortex/spiral twister effect on a 3D LED tree.
LEDs light up in a rotating helix that ascends or descends continuously.
"""
import os
import time
import math
import argparse
import pandas as pd
from rpi_ws281x import PixelStrip, Color
import ambient_brightness

parser = argparse.ArgumentParser(description="Vortex/Spiral Twister effect on 3D LED tree")
parser.add_argument("-i", "--interval", type=float, default=0.05,
                    help="Seconds between frames (frame rate)")
parser.add_argument("-r", "--rotations-per-sec", type=float, default=0.2,
                    help="Number of full rotations per second")
parser.add_argument("-t", "--turns", type=float, default=3.0,
                    help="Helix turns from bottom to top")
parser.add_argument("--reverse", action="store_true",
                    help="Rotate in reverse direction")
parser.add_argument("--range", type=float, default=1.0,
                    help="Fractional Z range to animate (0–1), default full height")
args = parser.parse_args()

INTERVAL        = args.interval
RPS             = args.rotations_per_sec
HELIX_TURNS     = args.turns
REVERSE         = -1.0 if args.reverse else 1.0
Z_RANGE_FRACTION= max(0.0, min(1.0, args.range))

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV = os.path.join(BASE_DIR, 'coordinates.csv')
df         = pd.read_csv(COORDS_CSV)
positions  = df[['X','Y','Z']].values.tolist()
LED_COUNT  = len(positions)

tree_zs    = [pos[2] for pos in positions]
tree_z_min = min(tree_zs)
tree_z_max = max(tree_zs)
tree_height= tree_z_max - tree_z_min

led_theta = []
led_znorm = []
for (x, y, z) in positions:
    theta = math.atan2(y, x) 
    z_norm = (z - tree_z_min) / tree_height if tree_height>0 else 0.0
    z_norm = z_norm * Z_RANGE_FRACTION
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
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))

start_time = time.perf_counter()
try:
    while True:
        now = time.perf_counter() - start_time
        spin_phase = REVERSE * 2*math.pi * RPS * now
        for i in range(LED_COUNT):
            theta = led_theta[i]
            zf    = led_znorm[i]
            phase = theta + spin_phase + 2*math.pi * HELIX_TURNS * (1 - zf)
            intensity = 0.5 * (1 + math.sin(phase))
            bval = int(max(0, min(1, intensity)) * 255)
            strip.setPixelColor(i, Color(bval, bval, bval))
        strip.show()
        time.sleep(INTERVAL)

except KeyboardInterrupt:
    clear_strip()
    strip.show()
