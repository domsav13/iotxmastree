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
buildStart_time      = 5.907982
Flash1_time          = 7.167060
LastIntroFlash_time  = 39.028514
Youuu_time           = 49.858378
PianoStarts_time     = 50.844046
BeatDrops_time       = 57.250889

events = [
    {"time": buildStart_time,   "label": "buildStart"},
    {"time": Flash1_time,       "label": "Flash1"},
    {"time": 12.445502,         "label": "Flash2"},
    {"time": 16.900702,         "label": "Flash3"},
    {"time": 20.581084,         "label": "Flash4"},
    {"time": 24.648874,         "label": "Flash5"},
    {"time": 27.663858,         "label": "Flash6"},
    {"time": 28.929250,         "label": "Flash7"},
    {"time": 31.483910,         "label": "Flash8"},
    {"time": 33.035807,         "label": "Flash9"},
    {"time": 35.399464,         "label": "Flash10"},
    {"time": LastIntroFlash_time, "label": "LastIntroFlash"},
    {"time": Youuu_time,        "label": "Youuuuuuu"},
    {"time": PianoStarts_time,  "label": "PianoStarts"},
    {"time": BeatDrops_time,    "label": "BeatDrops"},
    {"time": 63.370245,         "label": "BackVocalsStart"},
    {"time": 69.777088,         "label": "BackVocalsStop"},
    {"time": 76.841043,         "label": "BackVocal2Start"},
    {"time": 82.180078,         "label": "BackVocal2Stop"},
    # Additional events as needed…
]

# Hyperparameters for brightness ramp:
low_brightness_factor = 0.2   # Dim during Intro (before buildStart)
max_brightness_factor = 1.0   # Full brightness
post_flash_brightness = 0.3   # Brightness immediately after LastIntroFlash

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
gold_color   = intended_color((255, 215, 0))        # Gold
yellow_color = intended_color((255, 255, 0))        # Yellow
pink_color   = intended_color((255, 105, 180))      # Pink

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
# LED Effect Functions
# ====================================================
def flash_all():
    """Flashes all LEDs to gold at full intensity and then fades them out gradually."""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, gold_color)
    strip.show()
    time.sleep(0.15)
    fade_duration = 0.5
    fade_steps = 20
    fade_delay = fade_duration / fade_steps
    for step in range(fade_steps):
        factor = 1.0 - ((step + 1) / fade_steps)
        faded = scale_color(gold_color, factor)
        for i in range(LED_COUNT):
            strip.setPixelColor(i, faded)
        strip.show()
        time.sleep(fade_delay)

# Global variable to hold pulse state for independent LED pulsing.
pulse_state = None

def init_pulse_state():
    global pulse_state
    # Each LED gets its own random phase offset.
    # Also choose an initial base color from our palette.
    pulse_state = {
        'phases': [random.uniform(0, 2*math.pi) for _ in range(LED_COUNT)],
        'colors': [random.choice([white_color, yellow_color, red_color, green_color, pink_color])
                   for _ in range(LED_COUNT)]
    }

def pulse_fast(pulse_elapsed, pulse_speed):
    """
    Pulses each LED independently.
    For each LED, its brightness is determined by a sine wave with its unique phase,
    and its base color is randomly updated with a small probability.
    """
    global pulse_state
    if pulse_state is None:
        init_pulse_state()
    for i in range(LED_COUNT):
        # Compute brightness factor for this LED.
        brightness = 0.5 * (1 + math.sin(2 * math.pi * pulse_speed * pulse_elapsed + pulse_state['phases'][i]))
        # With a 10% chance per update, randomly reassign the base color.
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

# ====================================================
# Main LED Synchronization Loop
# ====================================================
def run_led_show():
    """
    Runs the LED synchronization loop.
      • From Intro until buildStart: slow spiral at low brightness.
      • From buildStart to Flash1: brightness ramps from low to full.
      • From Flash1 until LastIntroFlash: spiral at full brightness.
      • At LastIntroFlash, the LEDs dim, then from LastIntroFlash to Youuuuuuu,
        brightness ramps from the dim value (post_flash_brightness) to full brightness.
      • From PianoStarts until BeatDrops: independent fast pulse effect.
      • Flash events (gold flash) override the default effect.
    """
    start_time = time.time()
    triggered_events = set()
    spiral_offset = 0
    pulse_start_time = None
    global pulse_state
    pulse_state = None  # Reset pulse state on each show

    try:
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
                        # buildStart triggers brightness ramp.
                        pass
                    elif "PianoStarts" in label:
                        pulse_start_time = current_time
                    triggered_events.add(label)

            # Default effect before PianoStarts.
            if adjusted_elapsed < PianoStarts_time:
                if adjusted_elapsed < buildStart_time:
                    brightness_factor = low_brightness_factor
                    spiral_speed = 0.05
                elif adjusted_elapsed < Flash1_time:
                    ramp_fraction = (adjusted_elapsed - buildStart_time) / (Flash1_time - buildStart_time)
                    brightness_factor = low_brightness_factor + ramp_fraction * (max_brightness_factor - low_brightness_factor)
                    spiral_speed = 0.05
                elif adjusted_elapsed < LastIntroFlash_time:
                    brightness_factor = max_brightness_factor
                    spiral_speed = 0.05
                elif adjusted_elapsed < Youuu_time:
                    ramp_fraction = (adjusted_elapsed - LastIntroFlash_time) / (Youuu_time - LastIntroFlash_time)
                    brightness_factor = post_flash_brightness + ramp_fraction * (max_brightness_factor - post_flash_brightness)
                    spiral_speed = 0.05
                else:
                    brightness_factor = max_brightness_factor
                    spiral_speed = 0.05
                update_slow_spiral(spiral_offset, brightness_factor)
                spiral_offset += spiral_speed
            elif adjusted_elapsed < BeatDrops_time:
                if pulse_start_time is None:
                    pulse_start_time = current_time
                pulse_elapsed = current_time - pulse_start_time
                pulse_speed = 3.0
                pulse_fast(pulse_elapsed, pulse_speed)
            else:
                break

            time.sleep(0.05)
    except KeyboardInterrupt:
        pass

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
