#!/usr/bin/env python3
import os
import time
import random
import math
import pandas as pd
import ambient_brightness    # patches PixelStrip.show() to apply ambient dimming
from rpi_ws281x import PixelStrip, Color

# ─── LED & Coordinate Setup ────────────────────────────────────────────────────
BASE_DIR    = os.path.dirname(os.path.abspath(__file__))
COORDS_CSV  = os.path.join(BASE_DIR, 'coordinates.csv')
df          = pd.read_csv(COORDS_CSV)
positions   = df[['X','Y','Z']].values.tolist()
LED_COUNT   = len(positions)

# ─── Strip Configuration ───────────────────────────────────────────────────────
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

# ─── Snake Settings ────────────────────────────────────────────────────────────
SNAKE_LENGTH    = 15       # Number of LEDs in the snake
FRAME_DELAY     = 0.1      # Seconds between moves (~10 FPS)
NEIGHBORS_K     = 6        # Number of nearest neighbors for movement
MIN_SEG_BRIGHT  = 50       # Tail segment brightness
MAX_SEG_BRIGHT  = 255      # Head segment brightness

# Precompute neighbor indices for each LED based on Euclidean distance
dist_matrix = []
for i, p in enumerate(positions):
    dists = [(j, math.dist(p, q)) for j, q in enumerate(positions) if j != i]
    dists.sort(key=lambda x: x[1])
    dist_matrix.append([idx for idx, _ in dists[:NEIGHBORS_K]])

# Initialize snake body: start at random LED
snake = [random.randrange(LED_COUNT)]

def choose_next(head, body):
    """
    Pick a neighbor of 'head' not in 'body' if possible, else any neighbor.
    """
    neighs = dist_matrix[head]
    choices = [n for n in neighs if n not in body]
    return random.choice(choices) if choices else random.choice(neighs)

# ─── Main Loop ────────────────────────────────────────────────────────────────
try:
    while True:
        head = snake[-1]
        next_led = choose_next(head, snake)
        snake.append(next_led)
        if len(snake) > SNAKE_LENGTH:
            snake.pop(0)

        # Draw snake with gradient brightness
        strip.clear()
        for idx, led in enumerate(snake):
            # idx: 0 tail, -1 head
            frac = idx / (SNAKE_LENGTH - 1)
            bri  = int(MIN_SEG_BRIGHT + frac * (MAX_SEG_BRIGHT - MIN_SEG_BRIGHT))
            # Green snake: RGB = (0, bri, 0)
            strip.setPixelColor(led, Color(0, bri, 0))
        strip.show()  # ambient dimming applied here

        time.sleep(FRAME_DELAY)

except KeyboardInterrupt:
    strip.clear()
    strip.show()
