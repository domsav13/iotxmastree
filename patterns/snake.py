#!/usr/bin/env python3
import os
import time
import random
import math
import pandas as pd
import ambient_brightness    # patches PixelStrip.show() for ambient dimming
from rpi_ws281x import PixelStrip, Color

# ─── LED & Coordinate Setup ────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV  = os.path.join(BASE_DIR, 'coordinates.csv')
df          = pd.read_csv(COORDS_CSV)
positions   = df[['X','Y','Z']].values.tolist()
LED_COUNT   = len(positions)

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
    """Turn off all LEDs."""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))

# ─── Snake Settings ────────────────────────────────────────────────────────────
SNAKE_LENGTH    = 15       # Number of LEDs in the snake
FRAME_DELAY     = 0.1      # Seconds between moves (~10 FPS)
NEIGHBORS_K     = 6        # How many nearest neighbors to consider
MIN_SEG_BRIGHT  = 50
MAX_SEG_BRIGHT  = 255

# Precompute neighbor indices for each LED
dist_matrix = []
for i, p in enumerate(positions):
    dists = [(j, math.dist(p, q)) for j, q in enumerate(positions) if j != i]
    dists.sort(key=lambda x: x[1])
    dist_matrix.append([idx for idx, _ in dists[:NEIGHBORS_K]])

# Initialize snake body
snake = [random.randrange(LED_COUNT)]

def choose_next(head, body):
    """Pick next LED from neighbors, preferring ones not in the body."""
    neighs  = dist_matrix[head]
    choices = [n for n in neighs if n not in body]
    return random.choice(choices) if choices else random.choice(neighs)

# ─── Main Loop ────────────────────────────────────────────────────────────────
try:
    while True:
        head     = snake[-1]
        next_led = choose_next(head, snake)
        snake.append(next_led)
        if len(snake) > SNAKE_LENGTH:
            snake.pop(0)

        clear_strip()
        for idx, led in enumerate(snake):
            frac = idx / (SNAKE_LENGTH - 1)
            bri  = int(MIN_SEG_BRIGHT + frac * (MAX_SEG_BRIGHT - MIN_SEG_BRIGHT))
            strip.setPixelColor(led, Color(0, bri, 0))
        strip.show()

        time.sleep(FRAME_DELAY)

except KeyboardInterrupt:
    clear_strip()
    strip.show()
