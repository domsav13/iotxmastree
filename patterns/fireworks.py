#!/usr/bin/env python3
import time
import random
import math
import pandas as pd
from rpi_ws281x import PixelStrip, Color
import ambient_brightness

# ─── LED & Coordinate Setup ────────────────────────────────────────────────────
BASE_DIR   = __import__('os').path.dirname(__import__('os').path.abspath(__file__))
COORDS_CSV = __import__('os').path.join(BASE_DIR, 'coordinates.csv')
df         = pd.read_csv(COORDS_CSV)
df['led_index'] = df.index
LED_COUNT  = len(df)

# ─── Strip Configuration ───────────────────────────────────────────────────────
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

# ─── Fireworks Animation ───────────────────────────────────────────────────────
def animate_fireworks(interval=0.05,
                      firework_duration=0.75,
                      spawn_chance=0.05,
                      blast_radius_factor=0.5):
    """
    Loop forever, spawning overlapping firework bursts.
    """
    # Precompute tree dimensions and blast radius
    tree_x_min, tree_x_max = df['X'].min(), df['X'].max()
    tree_y_min, tree_y_max = df['Y'].min(), df['Y'].max()
    tree_z_min, tree_z_max = df['Z'].min(), df['Z'].max()
    max_dim = max(tree_x_max - tree_x_min,
                  tree_y_max - tree_y_min,
                  tree_z_max - tree_z_min)
    local_radius = blast_radius_factor * max_dim

    # Define color groups (GRB ordering for Color())
    group1 = [(0,255,0), (69,255,0), (255,255,0)]
    group2 = [(105,255,180), (0,128,128), (0,0,255)]
    group3 = [(0,0,255), (255,255,0), (255,255,255)]
    color_groups = [group1, group2, group3]

    active_fireworks = []

    prev_time = time.time()
    while True:
        now = time.time()
        dt  = now - prev_time
        prev_time = now

        # Spawn new fireworks probabilistically
        if random.random() < spawn_chance:
            center = df.sample(n=1).iloc[0]
            cx, cy, cz = center['X'], center['Y'], center['Z']
            # Determine which LEDs fall in this burst
            local_leds = []
            for _, row in df.iterrows():
                dx = row['X'] - cx
                dy = row['Y'] - cy
                dz = row['Z'] - cz
                if math.sqrt(dx*dx + dy*dy + dz*dz) <= local_radius:
                    local_leds.append(int(row['led_index']))
            if not local_leds:
                local_leds = [int(center['led_index'])]
            # Choose random colors for this burst
            chosen_group = random.choice(color_groups)
            colors = {idx: random.choice(chosen_group) for idx in local_leds}
            # Register the new firework
            active_fireworks.append({
                'local_leds': local_leds,
                'colors':      colors,
                'start_time':  now,
                'duration':    firework_duration
            })

        # Clear contributions
        contributions = [(0, 0, 0)] * LED_COUNT

        # Update and accumulate each active firework
        for fw in active_fireworks:
            age = now - fw['start_time']
            if age > fw['duration']:
                continue
            fade = 1.0 - (age / fw['duration'])
            for idx in fw['local_leds']:
                br, bg, bb = fw['colors'][idx]
                cr = int(br * fade)
                cg = int(bg * fade)
                cb = int(bb * fade)
                or_, og, ob = contributions[idx]
                contributions[idx] = (min(or_ + cr, 255),
                                     min(og + cg, 255),
                                     min(ob + cb, 255))

        # Remove completed fireworks
        active_fireworks = [
            fw for fw in active_fireworks
            if (now - fw['start_time']) < fw['duration']
        ]

        # Render the frame
        for i, (r, g, b) in enumerate(contributions):
            strip.setPixelColor(i, Color(r, g, b))
        strip.show()

        time.sleep(interval)

if __name__ == '__main__':
    animate_fireworks(
        interval=0.05,
        firework_duration=0.5,
        spawn_chance=0.5,
        blast_radius_factor=0.5
    )
