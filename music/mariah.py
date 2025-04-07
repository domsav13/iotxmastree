#!/usr/bin/env python3
import time
import colorsys
import random
import math
import pandas as pd
from rpi_ws281x import PixelStrip, Color
from flask import Flask, send_from_directory, render_template_string, jsonify
from threading import Thread

# ====================================================
# Hyperparameter: Latency Offset (in seconds)
# Adjust this value to compensate for any delay between Flask and the LED tree.
LATENCY_OFFSET = -0.5

# ====================================================
# LED Tree Configuration
# ====================================================
# Load LED coordinates from CSV (should have columns: X, Y, Z).
df = pd.read_csv('coordinates.csv')
LED_COUNT = len(df)

# LED strip configuration:
LED_PIN     = 18       # GPIO pin (supports PWM)
LED_FREQ_HZ = 800000   # LED signal frequency in hertz
LED_DMA     = 10       # DMA channel for signal generation
LED_BRIGHTNESS = 125   # Initial brightness (fixed, no ambient sensor)
LED_INVERT  = False    # Invert signal if needed
LED_CHANNEL = 0        # Use channel 0 for GPIO 18

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                   LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# ====================================================
# Timeline for Song Events (timestamps in seconds)
# Source: mariah_labels.txt :contentReference[oaicite:0]{index=0}
# ====================================================
events = [
    {"time": 5.907982,   "label": "buildStart"},
    {"time": 7.167060,   "label": "Flash1"},
    {"time": 12.445502,  "label": "Flash2"},
    {"time": 16.900702,  "label": "Flash3"},
    {"time": 20.581084,  "label": "Flash4"},
    {"time": 24.648874,  "label": "Flash5"},
    {"time": 27.663858,  "label": "Flash6"},
    {"time": 28.929250,  "label": "Flash7"},
    {"time": 31.483910,  "label": "Flash8"},
    {"time": 33.035807,  "label": "Flash9"},
    {"time": 35.399464,  "label": "Flash10"},
    {"time": 39.028514,  "label": "LastIntroFlash"},
    {"time": 49.858378,  "label": "Youuuuuuu"},
    {"time": 50.844046,  "label": "PianoStarts"},
    {"time": 57.250889,  "label": "BeatDrops"},
    {"time": 63.370245,  "label": "BackVocalsStart"},
    {"time": 69.777088,  "label": "BackVocalsStop"},
    {"time": 76.841043,  "label": "BackVocal2Start"},
    {"time": 82.180078,  "label": "BackVocal2Stop"},
    # Additional events can be added as needed…
]

# ====================================================
# LED Effect Functions
# ====================================================
def flash_all():
    """Flashes all LEDs brightly for a brief moment."""
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(255, 255, 255))
    strip.show()
    time.sleep(0.1)
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

def build_effect():
    """
    Represents the build: increase brightness to maximum.
    Here we set all LEDs to white at full brightness.
    """
    strip.setBrightness(LED_BRIGHTNESS)
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(255, 255, 255))
    strip.show()
    time.sleep(0.5)

def pulse_fast():
    """Pulses all LEDs quickly, simulating a fast heartbeat or piano start."""
    for _ in range(5):  # 5 rapid pulses
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(255, 255, 255))
        strip.show()
        time.sleep(0.05)
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()
        time.sleep(0.05)

def spiral_swirl():
    """
    Creates a spiral swirl effect of red and white.
    This is a placeholder effect that alternates colors along LED indices.
    """
    for _ in range(20):  # Duration of the swirl effect
        for i in range(LED_COUNT):
            if i % 2 == 0:
                color = Color(255, 0, 0)  # red
            else:
                color = Color(255, 255, 255)  # white
            strip.setPixelColor(i, color)
        strip.show()
        time.sleep(0.05)
        for i in range(LED_COUNT):
            if i % 2 == 0:
                color = Color(255, 255, 255)
            else:
                color = Color(255, 0, 0)
            strip.setPixelColor(i, color)
        strip.show()
        time.sleep(0.05)

def background_vocals_effect():
    """
    Adds a supporting color during background vocal intervals.
    For example, a subdued purple can complement the main effects.
    """
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(128, 0, 128))
    strip.show()

# ====================================================
# Main LED Synchronization Loop
# ====================================================
def run_led_show():
    """
    Runs the LED synchronization loop.
    This function is intended to run in a background thread while the song plays in the browser.
    """
    start_time = time.time()
    triggered_events = set()
    try:
        while True:
            # Adjust elapsed time by adding the latency offset.
            adjusted_elapsed = (time.time() - start_time) + LATENCY_OFFSET

            # Trigger events based on their timestamps.
            for event in events:
                if adjusted_elapsed >= event["time"] and event["label"] not in triggered_events:
                    label = event["label"]
                    print("Triggering event:", label, "at adjusted time", adjusted_elapsed, "seconds")
                    if "Flash" in label:
                        flash_all()
                    elif "buildStart" in label:
                        build_effect()
                    elif "PianoStarts" in label:
                        pulse_fast()
                    elif "BeatDrops" in label:
                        spiral_swirl()
                    elif "BackVocals" in label or "BackVocal" in label:
                        background_vocals_effect()
                    triggered_events.add(label)
            
            # End the loop after the final event.
            if adjusted_elapsed >= events[-1]["time"]:
                break
            time.sleep(0.01)
    except KeyboardInterrupt:
        pass

    # Turn off all LEDs when the show ends.
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
                // Play audio when the light show is triggered.
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
