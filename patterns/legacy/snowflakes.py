#!/usr/bin/env python3
import os
import time
import random
import math
import pandas as pd
from rpi_ws281x import PixelStrip, Color
import ambient_brightness    # patches PixelStrip.show() to apply ambient dimming

# ─── LED & Coordinate Setup ────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV  = os.path.join(BASE_DIR, 'coordinates.csv')
df          = pd.read_csv(COORDS_CSV)
df['led_index'] = df.index
positions   = df[['X','Y','Z']].values.tolist()
LED_COUNT   = len(positions)

# ─── Strip Configuration ───────────────────────────────────────────────────────
LED_PIN        = 18      # PWM pin (data)
LED_FREQ_HZ    = 800000  # signal frequency
LED_DMA        = 10      # DMA channel
LED_BRIGHTNESS = 125     # initial brightness (ambient_brightness will override)
LED_INVERT     = False
LED_CHANNEL    = 0

strip = PixelStrip(
    LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
    LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL
)
strip.begin()

def clear_strip():
    """Turn off all LEDs."""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))

def animate_snowflakes(csv_file, interval=0.05, num_snowflakes=5,
                       speed=0.1, threshold=1.0):
    """
    Animate white snowflakes falling forever.
    """
    # Determine tree bounds from the CSV.
    tree_x_min, tree_x_max = df['X'].min(), df['X'].max()
    tree_y_min, tree_y_max = df['Y'].min(), df['Y'].max()
    tree_z_min, tree_z_max = df['Z'].min(), df['Z'].max()

    # Initialize snowflake particles.
    snowflakes = []
    for _ in range(num_snowflakes):
        snowflakes.append({
            'x': random.uniform(tree_x_min, tree_x_max),
            'y': random.uniform(tree_y_min, tree_y_max),
            'z': tree_z_max
        })

    prev_time = time.time()

    while True:
        # --- Draw Phase ---
        clear_strip()

        # Light any LED close enough to a snowflake
        for idx, row in df.iterrows():
            led_x, led_y, led_z = row['X'], row['Y'], row['Z']
            for sf in snowflakes:
                dx = led_x - sf['x']
                dy = led_y - sf['y']
                dz = led_z - sf['z']
                if math.sqrt(dx*dx + dy*dy + dz*dz) <= threshold:
                    strip.setPixelColor(int(row['led_index']), Color(255, 255, 255))
                    break

        strip.show()
        time.sleep(interval)

        # --- Update Phase ---
        current_time = time.time()
        dt = current_time - prev_time
        prev_time = current_time

        for sf in snowflakes:
            sf['z'] -= speed * dt
            if sf['z'] < tree_z_min:
                # respawn at top
                sf['x'] = random.uniform(tree_x_min, tree_x_max)
                sf['y'] = random.uniform(tree_y_min, tree_y_max)
                sf['z'] = tree_z_max

if __name__ == '__main__':
    # Adjust parameters as desired
    animate_snowflakes(
        csv_file='coordinates.csv',
        interval=0.05,
        num_snowflakes=100,
        speed=10,
        threshold=1.0
    )
