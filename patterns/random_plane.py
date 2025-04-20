"""
Animate random colored planes traveling through a 3D LED tree, looping forever.
"""
import time
import math
import random
import pandas as pd
from rpi_ws281x import PixelStrip, Color
import ambient_brightness

BASE_DIR    = __import__('os').path.dirname(__import__('os').path.abspath(__file__))
COORDS_CSV  = __import__('os').path.join(BASE_DIR, 'coordinates.csv')
df          = pd.read_csv(COORDS_CSV)
df['led_index'] = df.index
positions   = df[['X','Y','Z']].values.tolist()
LED_COUNT   = len(positions)

LED_PIN        = 18
LED_FREQ_HZ    = 800000
LED_DMA        = 10
LED_BRIGHTNESS = 125
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

def animate_random_planes(interval=0.01, plane_speed=50.0, thickness_factor=0.1):
    """
    Loop forever animating random planes through the tree.

    interval: seconds between frames
    plane_speed: movement speed of plane along its normal
    thickness_factor: thickness fraction of the projection range
    """
    while True:
        A = random.uniform(-1, 1)
        B = random.uniform(-1, 1)
        C = random.uniform(-1, 1)
        norm = math.sqrt(A*A + B*B + C*C)
        if norm == 0:
            continue
        A /= norm; B /= norm; C /= norm

        projections = [A*x + B*y + C*z for (x, y, z) in positions]
        min_p = min(projections)
        max_p = max(projections)
        proj_range = max_p - min_p

        thickness = thickness_factor * proj_range

        D = min_p - thickness
        end_D = max_p + thickness
        plane_color = Color(random.randint(0,255),
                             random.randint(0,255),
                             random.randint(0,255))

        prev_time = time.time()
        while D < end_D:
            clear_strip()
            for idx, p in enumerate(projections):
                if abs(p + D) <= thickness / 2:
                    strip.setPixelColor(int(df.at[idx, 'led_index']), plane_color)
            strip.show()
            time.sleep(interval)
            now = time.time()
            dt = now - prev_time
            prev_time = now
            D += plane_speed * dt

if __name__ == '__main__':
    animate_random_planes(
        interval=0.01,
        plane_speed=25.0,
        thickness_factor=0.8
    )
