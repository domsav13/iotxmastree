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
# Load LED coordinates from CSV (CSV should have columns: X, Y, Z).
df = pd.read_csv('coordinates.csv')
LED_COUNT = len(df)
# Compute min and max Z values for the gradual lighting effect.
min_z = df["Z"].min()
max_z = df["Z"].max()

# LED strip configuration:
LED_PIN         = 18       # GPIO pin (supports PWM)
LED_FREQ_HZ     = 800000   # LED signal frequency in hertz
LED_DMA         = 10       # DMA channel for signal generation
LED_BRIGHTNESS  = 125      # Fixed brightness (no ambient sensor)
LED_INVERT      = False    # Invert signal if needed
LED_CHANNEL     = 0        # Use channel 0 for GPIO 18

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                   LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# ====================================================
# Timeline for Song Events (timestamps in seconds)
# Source: mariah_labels.txt :contentReference[oaicite:0]{index=0}
# ====================================================
# Key timestamps:
buildStart_time       = 5.907982
Flash1_time           = 7.167060
LastIntroFlash_time   = 39.028514
Youuu_time            = 49.858378
PianoStarts_time      = 50.844046
BeatDrops_time        = 57.250889
allI_time             = 92.284925   # "All I..." label

events = [
    {"time": buildStart_time,    "label": "buildStart"},
    {"time": Flash1_time,        "label": "Flash1"},
    {"time": 12.445502,          "label": "Flash2"},
    {"time": 16.900702,          "label": "Flash3"},
    {"time": 20.581084,          "label": "Flash4"},
    {"time": 24.648874,          "label": "Flash5"},
    {"time": 27.663858,          "label": "Flash6"},
    {"time": 28.929250,          "label": "Flash7"},
    {"time": 31.483910,          "label": "Flash8"},
    {"time": 33.035807,          "label": "Flash9"},
    {"time": 35.399464,          "label": "Flash10"},
    {"time": LastIntroFlash_time, "label": "LastIntroFlash"},
    {"time": Youuu_time,         "label": "Youuuuuuu"},
    {"time": PianoStarts_time,   "label": "PianoStarts"},
    {"time": BeatDrops_time,     "label": "BeatDrops"},
    {"time": allI_time,          "label": "All I..."},
    {"time": 63.370245,          "label": "BackVocalsStart"},
    {"time": 69.777088,          "label": "BackVocalsStop"},
    {"time": 76.841043,          "label": "BackVocal2Start"},
    {"time": 82.180078,          "label": "BackVocal2Stop"},
    # Additional events as needed…
]

# Define back vocal intervals.
back_vocals_start  = 63.370245
back_vocals_stop   = 69.777088
back_vocal2_start  = 76.841043
back_vocal2_stop   = 82.180078

# Hyperparameters for brightness ramp:
low_brightness_factor  = 0.2   # Dim during Intro (before buildStart)
max_brightness_factor  = 1.0   # Full brightness
post_flash_brightness  = 0.3   # Brightness immediately after LastIntroFlash

# Fast spiral speed for BeatDrops phase.
fast_spiral_speed = 0.2

# ====================================================
# Color Helpers (for GRB strips)
# ====================================================
def intended_color(rgb_tuple):
    """
    Converts an (R, G, B) tuple in standard RGB into a Color value for GRB strips.
    (Swaps red and green.)
    """
    r, g, b = rgb_tuple
    return Color(g, r, b)

# Define base colors (intended appearance):
red_color    = intended_color((255, 0, 0))         # Red
green_color  = intended_color((0, 255, 0))         # Green
white_color  = intended_color((255, 255, 255))     # White
gold_color   = intended_color((255, 215, 0))         # Gold
yellow_color = intended_color((255, 255, 0))         # Yellow
pink_color   = intended_color((255, 105, 180))       # Pink

# For the standard fast spiral, we use red, green, white.
# For accent mode (back vocals), define an accent palette.
accent_orange     = intended_color((255, 165, 0))    # Orange
accent_pink       = pink_color                        # Pink (reuse)
accent_purple     = intended_color((147, 112, 219))    # Medium purple
accent_yellow     = yellow_color                      # Yellow (reuse)
accent_light_blue = intended_color((173, 216, 230))    # Light blue
accent_red        = intended_color((255, 99, 71))      # Tomato red
accent_green      = intended_color((144, 238, 144))    # Light green

accent_palette = [accent_orange, accent_pink, accent_purple,
                  accent_yellow, accent_light_blue, accent_red, accent_green]

def scale_color(color, factor):
    """
    Scales a Color's brightness by factor (0.0 to 1.0).
    Decodes the GRB-encoded color, scales channels, and re-encodes.
    """
    blue  = color & 0xFF
    red   = (color >> 8) & 0xFF
    green = (color >> 16) & 0xFF
    red   = int(red * factor)
    green = int(green * factor)
    blue  = int(blue * factor)
    return Color(red, green, blue)

# ====================================================
# New Effect: Gradual Bottom-Up Lighting with Twinkle
# ====================================================
def gradual_bottom_up_effect(adjusted_elapsed, flash1_time):
    """
    Gradually lights up the tree from the bottom up.
    Based on the Z-coordinate of each LED, a fraction of the tree is lit.
    LEDs with lower normalized Z values light up first.
    A random twinkle effect is applied (random brightness modulation).
    By flash1_time, the entire tree is lit.
    """
    # Determine the fraction of the tree to light up.
    fraction = min(adjusted_elapsed / flash1_time, 1.0)
    for i in range(LED_COUNT):
        # Get the Z coordinate for LED i (assumes row order corresponds to LED index).
        z = df.iloc[i]["Z"]
        # Normalize the Z coordinate.
        norm_z = (z - min_z) / (max_z - min_z)
        # If the normalized Z is below the fraction, light up the LED with twinkle.
        if norm_z <= fraction:
            # Twinkle factor varies randomly between 0.8 and 1.0.
            twinkle = random.uniform(0.8, 1.0)
            color = scale_color(white_color, twinkle)
        else:
            color = Color(0, 0, 0)
        strip.setPixelColor(i, color)
    strip.show()

# ====================================================
# LED Effect Functions (Existing)
# ====================================================
def flash_all():
    """Flashes all LEDs to gold at full intensity and then fades them out gradually."""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, gold_color)
    strip.show()
    time.sleep(0.15)
    fade_duration = 0.75
    fade_steps = 20
    fade_delay = fade_duration / fade_steps
    for step in range(fade_steps):
        factor = 1.0 - ((step + 1) / fade_steps)
        faded = scale_color(gold_color, factor)
        for i in range(LED_COUNT):
            strip.setPixelColor(i, faded)
        strip.show()
        time.sleep(fade_delay)

# Global pulse state for independent LED pulsing.
pulse_state = None

def init_pulse_state():
    global pulse_state
    pulse_state = {
        'phases': [random.uniform(0, 2*math.pi) for _ in range(LED_COUNT)],
        'colors': [random.choice([white_color, yellow_color, red_color, green_color, pink_color])
                   for _ in range(LED_COUNT)]
    }

def pulse_fast(pulse_elapsed, pulse_speed):
    """
    Pulses each LED independently.
    Each LED uses its unique phase offset for a sine-wave brightness,
    and its base color is randomly updated with a small probability.
    """
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
    """
    Updates LEDs with a slow spiral effect cycling through red, green, and white.
    'offset' rotates the color assignment; brightness_factor scales each color.
    """
    for i in range(LED_COUNT):
        color_index = (i + int(offset)) % 3
        if color_index == 0:
            base = red_color
        elif color_index == 1:
            base = green_color
        else:
            base = white_color
        scaled = scale_color(base, brightness_factor)
        strip.setPixelColor(i, scaled)
    strip.show()

def update_fast_spiral(offset, brightness_factor=1.0, accent=False):
    """
    Updates LEDs with a fast spiral effect.
    If accent is False, it cycles through the standard palette: red, green, white.
    If accent is True, it uses the accent palette.
    'offset' rotates the color assignment; brightness_factor scales each color.
    """
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
            if color_index == 0:
                base = red_color
            elif color_index == 1:
                base = green_color
            else:
                base = white_color
            scaled = scale_color(base, brightness_factor)
            strip.setPixelColor(i, scaled)
    strip.show()

# ====================================================
# Main LED Synchronization Loop
# ====================================================
def run_led_show():
    """
    Runs the LED synchronization loop.
      • From Intro until Flash1: the tree gradually lights up from the bottom with twinkle.
      • From Flash1 until LastIntroFlash: the initial spiral effect (slow spiral) runs.
      • At LastIntroFlash, the LEDs dim, then from LastIntroFlash to Youuuuuuu,
        brightness ramps from the dim value (post_flash_brightness) to full brightness.
      • From PianoStarts until BeatDrops: independent fast pulse effect.
      • From BeatDrops until "All I...": fast spiral effect.
           During back vocal intervals, accent colors are incorporated.
      • Flash events (gold flash) override the default effect.
    """
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
                    pass  # buildStart could trigger a ramp if needed.
                elif "PianoStarts" in label:
                    pulse_start_time = current_time
                triggered_events.add(label)

        # Effect Branches:
        if adjusted_elapsed < Flash1_time:
            # From Intro to Flash1: gradually light up from the bottom with twinkle.
            gradual_bottom_up_effect(adjusted_elapsed, Flash1_time)
        elif adjusted_elapsed < PianoStarts_time:
            # From Flash1 until PianoStarts: run the initial (slow) spiral effect.
            brightness_factor = max_brightness_factor
            spiral_speed = 0.05
            update_slow_spiral(spiral_offset, brightness_factor)
            spiral_offset += spiral_speed
        elif adjusted_elapsed < BeatDrops_time:
            # From PianoStarts until BeatDrops: independent fast pulse effect.
            if pulse_start_time is None:
                pulse_start_time = current_time
            pulse_elapsed = current_time - pulse_start_time
            pulse_speed = 3.0
            pulse_fast(pulse_elapsed, pulse_speed)
        elif adjusted_elapsed < allI_time:
            # From BeatDrops until "All I...": fast spiral effect.
            brightness_factor = max_brightness_factor
            # Check for back vocal intervals to enable accent mode.
            if ((adjusted_elapsed >= 63.370245 and adjusted_elapsed < 69.777088) or
                (adjusted_elapsed >= 76.841043 and adjusted_elapsed < 82.180078)):
                accent = True
            else:
                accent = False
            update_fast_spiral(spiral_offset, brightness_factor, accent)
            spiral_offset += fast_spiral_speed
        else:
            break

        time.sleep(0.05)

    # Turn off LEDs when finished.
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
