import os
import time
import math
import pandas as pd
from rpi_ws281x import PixelStrip, Color
import ambient_brightness

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV = os.path.join(BASE_DIR, 'coordinates.csv')
df = pd.read_csv(COORDS_CSV)
LED_COUNT = len(df)

LED_PIN        = 18      # PWM pin
LED_FREQ_HZ    = 800000  # LED signal frequency in hertz
LED_DMA        = 10      # DMA channel
LED_BRIGHTNESS = 255     # initial brightness (ambient_brightness overrides per frame)
LED_INVERT     = False
LED_CHANNEL    = 0

strip = PixelStrip(
    LED_COUNT, LED_PIN, LED_FREQ_HZ,
    LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL
)
strip.begin()

BEAT_PERIOD     = 1.0    # seconds per heartbeat cycle (~60 BPM)
MIN_INTENSITY   = 20     # LED value at trough
MAX_INTENSITY   = 255    # LED value at peak
FRAME_DELAY     = 0.02   # ~50 FPS

def heartbeat_envelope(t, period=BEAT_PERIOD):
    """
    Double‑pulse heartbeat curve using two Gaussians:
     - Primary pulse at t=0
     - Secondary (softer) at t=0.3*period
    Returns a value in [0,1].
    """
    sigma1 = period * 0.08
    sigma2 = period * 0.08
    p1 = math.exp(-0.5 * (t / sigma1) ** 2)
    p2 = 0.6 * math.exp(-0.5 * ((t - 0.3 * period) / sigma2) ** 2)
    val = p1 + p2
    return min(val, 1.0)

try:
    start_time = time.time()
    while True:
        elapsed = (time.time() - start_time) % BEAT_PERIOD
        env = heartbeat_envelope(elapsed)
        brightness = int(MIN_INTENSITY + env * (MAX_INTENSITY - MIN_INTENSITY))
        color = Color(0, brightness, 0)
        for i in range(LED_COUNT):
            strip.setPixelColor(i, color)
        strip.show()  
        time.sleep(FRAME_DELAY)

except KeyboardInterrupt:
    strip.clear()
    strip.show()
