#!/usr/bin/env python3
import time
import math
import random
import pandas as pd
from rpi_ws281x import PixelStrip, Color
from flask import Flask, send_from_directory, render_template_string, jsonify
from threading import Thread

# ====================================================
# Hyperparameter: Latency Offset (in seconds)
LATENCY_OFFSET = -0.5

# ====================================================
# LED Tree Configuration
# ====================================================
df = pd.read_csv('coordinates.csv')  # CSV should have columns: X, Y, Z.
LED_COUNT = len(df)
min_z = df["Z"].min()
max_z = df["Z"].max()

# LED strip configuration:
LED_PIN         = 18       # GPIO pin (supports PWM)
LED_FREQ_HZ     = 800000   # Frequency in hertz
LED_DMA         = 10       # DMA channel for signal generation
LED_BRIGHTNESS  = 125      # Fixed brightness (no ambient sensor)
LED_INVERT      = False    # Invert signal if needed
LED_CHANNEL     = 0        # Use channel 0

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                   LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# ====================================================
# Timeline (timestamps in seconds from mariah_labels.txt)
# ====================================================
buildStart_time       = 5.907982
Flash1_time           = 7.167060
LastIntroFlash_time   = 39.028514
Youuu_time            = 49.858378
PianoStarts_time      = 50.844046
BeatDrops_time        = 57.250889
BackVocalsStart       = 63.370245
BackVocalsStop        = 69.777088
BackVocal2Start       = 76.841043
BackVocal2Stop        = 82.180078
All_I_time            = 92.284925   # "All I..."
youuuu_label_1        = 98.449425   # first "you... Youuuuuu"
BackVocal3Start       = 108.247176
BackVocal3Stop        = 114.172523
BackVocal4Start       = 121.508666
BackVocal4Stop        = 127.095422
All_dots_time         = 137.298746  # "All...."
youuuu_label_2        = 142.998365  # second "you... Youuuuu"

# Define back vocal intervals for phase 4 (original):
back_vocals_phase4 = [(BackVocalsStart, BackVocalsStop), (BackVocal2Start, BackVocal2Stop)]
# Define new back vocal intervals for phase 5:
back_vocals_phase5 = [(BackVocal3Start, BackVocal3Stop), (BackVocal4Start, BackVocal4Stop)]

# ====================================================
# Hyperparameters for Brightness Ramp
low_brightness_factor  = 0.2   # Before buildStart
max_brightness_factor  = 1.0   # Full brightness
post_flash_brightness  = 0.3   # Immediately after LastIntroFlash

# Fast spiral speed for fast spiral phases.
fast_spiral_speed = 0.2

# ====================================================
# Color Helpers (for GRB strips)
# ====================================================
def intended_color(rgb_tuple):
    r, g, b = rgb_tuple
    return Color(g, r, b)  # Swap red and green

# Standard base colors:
red_color    = intended_color((255, 0, 0))        # Red
green_color  = intended_color((0, 255, 0))        # Green
white_color  = intended_color((255, 255, 255))    # White
gold_color   = intended_color((255, 215, 0))        # Gold
yellow_color = intended_color((255, 255, 0))        # Yellow
pink_color   = intended_color((255, 105, 180))      # Pink

# Accent palette for phase 4 (original accent):
accent_orange     = intended_color((255, 165, 0))   # Orange
accent_pink       = pink_color                       # Pink (reuse)
accent_purple     = intended_color((147, 112, 219))   # Medium purple
accent_light_blue = intended_color((173, 216, 230))   # Light blue
accent_red        = intended_color((255, 99, 71))     # Tomato red
accent_green      = intended_color((144, 238, 144))   # Light green

accent_palette = [accent_orange, accent_pink, accent_purple,
                  yellow_color, accent_light_blue, accent_red, accent_green]

# New palette for phase 5 (normal):
new_light_blue = intended_color((173, 216, 230))
new_palette = [new_light_blue, pink_color, accent_purple]
# New accent palette for phase 5:
new_accent_palette = [red_color, green_color, yellow_color, white_color]

def scale_color(color, factor):
    blue  = color & 0xFF
    red   = (color >> 8) & 0xFF
    green = (color >> 16) & 0xFF
    return Color(int(red * factor), int(green * factor), int(blue * factor))

# ====================================================
# New Effect: Gradual Bottom-Up Lighting with White & Pink Twinkle
# ====================================================
def gradual_bottom_up_effect(adjusted_elapsed, flash1_time):
    fraction = min(adjusted_elapsed / flash1_time, 1.0)
    for i in range(LED_COUNT):
        z = df.iloc[i]["Z"]
        norm_z = (z - min_z) / (max_z - min_z)
        if norm_z <= fraction:
            chosen_color = random.choice([white_color, pink_color])
            twinkle = random.uniform(0.8, 1.0)
            color = scale_color(chosen_color, twinkle)
        else:
            color = Color(0, 0, 0)
        strip.setPixelColor(i, color)
    strip.show()

# ====================================================
# Existing LED Effect Functions
# ====================================================
def flash_all():
    for i in range(LED_COUNT):
        strip.setPixelColor(i, gold_color)
    strip.show()
    time.sleep(0.15)
    fade_duration = 0.6
    fade_steps = 20
    fade_delay = fade_duration / fade_steps
    for step in range(fade_steps):
        factor = 1.0 - ((step + 1) / fade_steps)
        faded = scale_color(gold_color, factor)
        for i in range(LED_COUNT):
            strip.setPixelColor(i, faded)
        strip.show()
        time.sleep(fade_delay)

# Global pulse state for independent pulsing.
pulse_state = None

def init_pulse_state():
    global pulse_state
    pulse_state = {
        'phases': [random.uniform(0, 2*math.pi) for _ in range(LED_COUNT)],
        'colors': [random.choice([white_color, yellow_color, red_color, green_color, pink_color])
                   for _ in range(LED_COUNT)]
    }

def pulse_fast(pulse_elapsed, pulse_speed):
    global pulse_state
    if pulse_state is None:
        init_pulse_state()
    for i in range(LED_COUNT):
        brightness = 0.5 * (1 + math.sin(2 * math.pi * pulse_speed * pulse_elapsed + pulse_state['phases'][i]))
        if random.random() < 0.1:
            pulse_state['colors'][i] = random.choice([white_color, yellow_color, red_color, green_color, pink_color])
        scaled = scale_color(pulse_state['colors'][i], brightness)
        strip.setPixelColor(i, scaled)
    strip.show()

def update_slow_spiral(offset, brightness_factor=1.0):
    for i in range(LED_COUNT):
        color_index = (i + int(offset)) % 3
        base = red_color if color_index == 0 else green_color if color_index == 1 else white_color
        scaled = scale_color(base, brightness_factor)
        strip.setPixelColor(i, scaled)
    strip.show()

def update_fast_spiral(offset, brightness_factor=1.0, accent=False):
    if accent:
        mod_val = len(accent_palette)
        for i in range(LED_COUNT):
            color_index = (i + int(offset)) % mod_val
            base = accent_palette[color_index]
            scaled = scale_color(base, brightness_factor)
            strip.setPixelColor(i, scaled)
    else:
        for i in range(LED_COUNT):
            color_index = (i + int(offset)) % 3
            base = red_color if color_index == 0 else green_color if color_index == 1 else white_color
            scaled = scale_color(base, brightness_factor)
            strip.setPixelColor(i, scaled)
    strip.show()

def update_fast_spiral_new(offset, brightness_factor=1.0, accent=False):
    if accent:
        mod_val = len(new_accent_palette)
        for i in range(LED_COUNT):
            color_index = (i + int(offset)) % mod_val
            base = new_accent_palette[color_index]
            scaled = scale_color(base, brightness_factor)
            strip.setPixelColor(i, scaled)
    else:
        mod_val = len(new_palette)
        for i in range(LED_COUNT):
            color_index = (i + int(offset)) % mod_val
            base = new_palette[color_index]
            scaled = scale_color(base, brightness_factor)
            strip.setPixelColor(i, scaled)
    strip.show()

# ====================================================
# Main LED Synchronization Loop
# ====================================================
def run_led_show():
    # Define additional phase timestamps:
    # Phase 4: from BeatDrops (57.250889) to you... Youuuuuu (first occurrence) at 98.449425.
    # Phase 5: from you... Youuuuuu (first) to you... Youuuuuu (second) at 142.998365.
    youuuu_label_1 = 98.449425
    youuuu_label_2 = 142.998365

    start_time = time.time()
    triggered_events = set()
    spiral_offset = 0
    pulse_start_time = None
    global pulse_state
    pulse_state = None  # Reset pulse state on each show

    while True:
        current_time = time.time()
        adjusted_elapsed = (current_time - start_time) + LATENCY_OFFSET

        # Trigger timeline events.
        for event in events:
            if adjusted_elapsed >= event["time"] and event["label"] not in triggered_events:
                label = event["label"]
                print("Triggering event:", label, "at adjusted time", adjusted_elapsed)
                if "Flash" in label:
                    flash_all()
                elif "buildStart" in label:
                    pass
                elif "PianoStarts" in label:
                    pulse_start_time = current_time
                triggered_events.add(label)

        # Phase 1: Intro to Flash1.
        if adjusted_elapsed < Flash1_time:
            gradual_bottom_up_effect(adjusted_elapsed, Flash1_time)
        # Phase 2: Flash1 to PianoStarts.
        elif adjusted_elapsed < PianoStarts_time:
            brightness_factor = max_brightness_factor
            spiral_speed = 0.05
            update_slow_spiral(spiral_offset, brightness_factor)
            spiral_offset += spiral_speed
        # Phase 3: PianoStarts to BeatDrops.
        elif adjusted_elapsed < BeatDrops_time:
            if pulse_start_time is None:
                pulse_start_time = current_time
            pulse_elapsed = current_time - pulse_start_time
            pulse_speed = 3.0
            pulse_fast(pulse_elapsed, pulse_speed)
        # Phase 4: BeatDrops to you... Youuuuuu (first occurrence).
        elif adjusted_elapsed < youuuu_label_1:
            brightness_factor = max_brightness_factor
            # Use original back vocal intervals for accent in phase 4.
            accent = any(start <= adjusted_elapsed < stop for (start, stop) in back_vocals_phase4)
            update_fast_spiral(spiral_offset, brightness_factor, accent)
            spiral_offset += fast_spiral_speed
        # Phase 5: you... Youuuuuu (first) to you... Youuuuuu (second).
        elif adjusted_elapsed < youuuu_label_2:
            brightness_factor = max_brightness_factor
            # Use new back vocal intervals for accent in phase 5.
            accent = any(start <= adjusted_elapsed < stop for (start, stop) in back_vocals_phase5)
            update_fast_spiral_new(spiral_offset, brightness_factor, accent)
            spiral_offset += fast_spiral_speed
        else:
            break

        time.sleep(0.05)

    # Turn off LEDs when the show ends.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

# ====================================================
# Flask Web Application
# ====================================================
app = Flask(__name__)
led_thread = None

@app.route('/')
def index():
    html = """
    <!doctype html>
    <html>
      <head>
        <title>LED Light Show Synchronized to Song</title>
        <script>
          function startShow() {
            fetch('/start', {method: 'POST'})
              .then(response => response.json())
              .then(data => {
                console.log(data);
                var audio = document.getElementById('audio');
                audio.play();
              })
              .catch(err => console.error(err));
          }
        </script>
      </head>
      <body>
        <h1>LED Light Show Synchronized to Song</h1>
        <button onclick="startShow()">Start Light Show</button>
        <br><br>
        <audio id="audio" controls>
          <source src="/audio/mariah.mp3" type="audio/mpeg">
          Your browser does not support the audio element.
        </audio>
      </body>
    </html>
    """
    return render_template_string(html)

@app.route('/start', methods=['POST'])
def start():
    global led_thread
    if led_thread is None or not led_thread.is_alive():
        led_thread = Thread(target=run_led_show)
        led_thread.daemon = True
        led_thread.start()
        return jsonify({"status": "LED light show started"})
    else:
        return jsonify({"status": "LED light show already running"})

@app.route('/audio/<path:filename>')
def audio(filename):
    return send_from_directory('audio', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
