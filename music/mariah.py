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
# ====================================================
LATENCY_OFFSET = -0.5

# ====================================================
# LED Tree Configuration
# ====================================================
df = pd.read_csv('coordinates.csv')  # CSV must have columns: X, Y, Z.
LED_COUNT = len(df)
min_z = df["Z"].min()
max_z = df["Z"].max()

# LED strip configuration:
LED_PIN         = 18
LED_FREQ_HZ     = 800000
LED_DMA         = 10
LED_BRIGHTNESS  = 125
LED_INVERT      = False
LED_CHANNEL     = 0

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                   LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# ====================================================
# Timeline for Song Events (timestamps from mariah_labels.txt)
# ====================================================
buildStart_time       = 5.907982
Flash1_time           = 7.167060
LastIntroFlash_time   = 39.028514
Youuu_time            = 49.858378
PianoStarts_time      = 50.844046
BeatDrops_time        = 57.250889
allI_time             = 92.284925   # "All I..." label
youuuu_label_1        = 98.449425   # first "you... Youuuuuu"
BridgeStart_time      = 147.005028  # BridgeStart
BridgeEnd_time        = 171.383597  # BridgeEnd
FinalAll_time         = 195.084983  # "FinalAll..." label
youuuuHighNote1       = 201.574649
HighNote2             = 207.951450
HighNote3             = 214.949002
FadeOut_time          = 219.068529
End_time              = 237.126728

# Back vocal intervals for Phase 4:
BackVocalsStart       = 63.370245
BackVocalsStop        = 69.777088
BackVocal2Start       = 76.841043
BackVocal2Stop        = 82.180078
back_vocals_phase4 = [(BackVocalsStart, BackVocalsStop), (BackVocal2Start, BackVocal2Stop)]

# Back vocal intervals for Phase 5:
BackVocal3Start       = 108.247176
BackVocal3Stop        = 114.172523
BackVocal4Start       = 121.508666
BackVocal4Stop        = 127.095422
back_vocals_phase5 = [(BackVocal3Start, BackVocal3Stop), (BackVocal4Start, BackVocal4Stop)]

# Back vocal interval for Phase 7:
BackVocal4Start_phase7 = 179.114763
BackVocal4Stop_phase7  = 184.757951
back_vocals_phase7 = [(BackVocal4Start_phase7, BackVocal4Stop_phase7)]

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
    {"time": youuuu_label_1,     "label": "you... Youuuuuu"},
    {"time": BridgeStart_time,   "label": "BridgeStart"},
    {"time": BridgeEnd_time,     "label": "BridgeEnd"},
    {"time": FinalAll_time,      "label": "FinalAll..."},
    {"time": youuuuHighNote1,    "label": "youuuuHighNote1"},
    {"time": HighNote2,          "label": "HighNote2"},
    {"time": HighNote3,          "label": "HighNote3"},
    {"time": FadeOut_time,       "label": "FadeOut"},
    {"time": End_time,           "label": "End"},
    {"time": BackVocalsStart,    "label": "BackVocalsStart"},
    {"time": BackVocalsStop,     "label": "BackVocalsStop"},
    {"time": BackVocal2Start,    "label": "BackVocal2Start"},
    {"time": BackVocal2Stop,     "label": "BackVocal2Stop"},
    {"time": BackVocal3Start,    "label": "BackVocal3Start"},
    {"time": BackVocal3Stop,     "label": "BackVocal3Stop"},
    {"time": BackVocal4Start,    "label": "BackVocal4Start"},
    {"time": BackVocal4Stop,     "label": "BackVocal4Stop"},
]

# ====================================================
# Hyperparameters for Brightness Ramp and Spiral Speeds
# ====================================================
low_brightness_factor  = 0.2
max_brightness_factor  = 1.0
post_flash_brightness  = 0.3

fast_spiral_speed = 0.05   # Use same speed as the initial slow spiral.
fast_spiral_speed2 = 0.3   # For Phase 7 (faster)

# Global final phase parameters (for Final Section).
final_spiral_speed = 0.2   # Initial final spiral speed.
final_brightness = 0.8     # Initial final brightness.

# ====================================================
# Color Helpers (for GRB strips) – GRB ordering assumed.
# ====================================================
def intended_color(rgb_tuple):
    r, g, b = rgb_tuple
    return Color(g, r, b)

red_color    = intended_color((255, 0, 0))
green_color  = intended_color((0, 255, 0))
white_color  = intended_color((255, 255, 255))
gold_color   = intended_color((255, 215, 0))
yellow_color = intended_color((255, 255, 0))
pink_color   = intended_color((255, 105, 180))

accent_orange     = intended_color((255, 165, 0))
accent_pink       = pink_color
accent_purple     = intended_color((147, 112, 219))
accent_light_blue = intended_color((173, 216, 230))
accent_red        = intended_color((255, 99, 71))
accent_green      = intended_color((144, 238, 144))
accent_palette = [accent_orange, accent_pink, accent_purple,
                  yellow_color, accent_light_blue, accent_red, accent_green]

new_light_blue = intended_color((173, 216, 230))
pastel_green = intended_color((100, 240, 100))
light_salmon = intended_color((255, 160, 122))
lavender = intended_color((230, 230, 250))
new_palette = [new_light_blue, pink_color, accent_purple, pastel_green, light_salmon, lavender]
new_accent_palette = [red_color, green_color, yellow_color, white_color]

bright_palette = [white_color, yellow_color, pink_color, intended_color((0,191,255)), green_color, red_color]

def scale_color(color, factor):
    blue  = color & 0xFF
    red   = (color >> 8) & 0xFF
    green = (color >> 16) & 0xFF
    return Color(int(red * factor), int(green * factor), int(blue * factor))

# ====================================================
# New Helper: Blend Two Colors for Accent Blending
# ====================================================
def blend_colors(c1, c2, t):
    r1 = (c1 >> 8) & 0xFF
    g1 = (c1 >> 16) & 0xFF
    b1 = c1 & 0xFF
    r2 = (c2 >> 8) & 0xFF
    g2 = (c2 >> 16) & 0xFF
    b2 = c2 & 0xFF
    r = int(r1 * (1-t) + r2 * t)
    g = int(g1 * (1-t) + g2 * t)
    b = int(b1 * (1-t) + b2 * t)
    return Color(r, g, b)

# ====================================================
# New Effect: Bridge Transition Twinkle (Phase 6)
# ====================================================
def bridge_transition_effect(adjusted_elapsed, bridge_start, bridge_end, offset, brightness_factor):
    t = (adjusted_elapsed - bridge_start) / (bridge_end - bridge_start)
    for i in range(LED_COUNT):
        mod_val = len(new_palette)
        color_index = (i + int(offset)) % mod_val
        spiral_color = scale_color(new_palette[color_index], brightness_factor)
        random_twinkle = random.uniform(0.8, 1.0)
        twinkle_color = scale_color(random.choice(bright_palette), brightness_factor * random_twinkle)
        final_color = blend_colors(spiral_color, twinkle_color, t)
        strip.setPixelColor(i, final_color)
    strip.show()

# ====================================================
# New Effect: Final Section Spiral and Fadeout (Phases 8 & 9)
# ====================================================
def update_final_spiral(offset, brightness_factor, base_speed):
    # Create a spiral pattern using alternating pink and white.
    for i in range(LED_COUNT):
        base = pink_color if (i % 2 == 0) else white_color
        blended = blend_colors(base, green_color, 0.5)
        final_color = scale_color(blended, brightness_factor)
        strip.setPixelColor(i, final_color)
    strip.show()

def update_final_fadeout(offset, brightness_factor, fade_progress):
    current_brightness = brightness_factor * (1 - fade_progress)
    for i in range(LED_COUNT):
        base = pink_color if (i % 2 == 0) else white_color
        blended = blend_colors(base, green_color, 0.5)
        final_color = scale_color(blended, current_brightness)
        strip.setPixelColor(i, final_color)
    strip.show()

# ====================================================
# Existing Effect: Gradual Bottom-Up Lighting with White & Pink Twinkle (Phase 1)
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
# Existing Effects: Flash, Pulse, Slow Spiral, Fast Spiral, etc.
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
            standard_index = (i + int(offset)) % 3
            standard_base = red_color if standard_index == 0 else green_color if standard_index == 1 else white_color
            blended = blend_colors(standard_base, base, 0.5)
            final_color = scale_color(blended, brightness_factor)
            strip.setPixelColor(i, final_color)
    else:
        for i in range(LED_COUNT):
            color_index = (i + int(offset)) % 3
            base = red_color if color_index == 0 else green_color if color_index == 1 else white_color
            final_color = scale_color(base, brightness_factor)
            strip.setPixelColor(i, final_color)
    strip.show()

def update_fast_spiral_new(offset, brightness_factor=1.0, accent=False):
    if accent:
        mod_val = len(new_accent_palette)
        for i in range(LED_COUNT):
            color_index = (i + int(offset)) % mod_val
            base = new_accent_palette[color_index]
            standard_index = (i + int(offset)) % len(new_palette)
            standard_base = new_palette[standard_index]
            blended = blend_colors(standard_base, base, 0.5)
            final_color = scale_color(blended, brightness_factor)
            strip.setPixelColor(i, final_color)
    else:
        mod_val = len(new_palette)
        for i in range(LED_COUNT):
            color_index = (i + int(offset)) % mod_val
            base = new_palette[color_index]
            final_color = scale_color(base, brightness_factor)
            strip.setPixelColor(i, final_color)
    strip.show()

def update_fast_spiral_phase7(offset, brightness_factor=1.0, accent=False):
    phase7_accent = [pink_color, intended_color((255,165,0)), intended_color((173,216,230))]
    for i in range(LED_COUNT):
        color_index = (i + int(offset)) % 3
        standard_base = red_color if color_index == 0 else green_color if color_index == 1 else white_color
        if accent:
            accent_index = (i + int(offset)) % len(phase7_accent)
            accent_color_value = phase7_accent[accent_index]
            blended = blend_colors(standard_base, accent_color_value, 0.5)
            final_color = scale_color(blended, brightness_factor)
        else:
            final_color = scale_color(standard_base, brightness_factor)
        strip.setPixelColor(i, final_color)
    strip.show()

# ====================================================
# Main LED Synchronization Loop
# ====================================================
def run_led_show():
    global events  # Use the global events variable.
    # Final Section (Phases 8 & 9) boundaries:
    # Phase 8: FinalAll... → FadeOut.
    # Phase 9: FadeOut → End.
    global final_spiral_speed, final_brightness
    final_spiral_speed = 0.2
    final_brightness = 0.8

    start_time = time.time()
    triggered_events = set()
    spiral_offset = 0
    pulse_start_time = None
    global pulse_state
    pulse_state = None

    while True:
        current_time = time.time()
        adjusted_elapsed = (current_time - start_time) + LATENCY_OFFSET

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
                elif label == "youuuuHighNote1":
                    final_spiral_speed = 0.3
                    final_brightness = 0.9
                elif label == "HighNote2":
                    final_spiral_speed = 0.4
                    final_brightness = 1.0
                elif label == "HighNote3":
                    final_spiral_speed = 0.5
                    final_brightness = 1.0
                triggered_events.add(label)

        if adjusted_elapsed < Flash1_time:
            gradual_bottom_up_effect(adjusted_elapsed, Flash1_time)
        elif adjusted_elapsed < PianoStarts_time:
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
        elif adjusted_elapsed < youuuu_label_1:
            brightness_factor = max_brightness_factor
            accent = any(start <= adjusted_elapsed < stop for (start, stop) in back_vocals_phase4)
            update_fast_spiral(spiral_offset, brightness_factor, accent)
            spiral_offset += fast_spiral_speed
        elif adjusted_elapsed < BridgeStart_time:
            brightness_factor = max_brightness_factor
            accent = any(start <= adjusted_elapsed < stop for (start, stop) in back_vocals_phase5)
            update_fast_spiral_new(spiral_offset, brightness_factor, accent)
            spiral_offset += fast_spiral_speed
        elif adjusted_elapsed < BridgeEnd_time:
            bridge_transition_effect(adjusted_elapsed, BridgeStart_time, BridgeEnd_time, spiral_offset, max_brightness_factor)
            spiral_offset += 0.01
        elif adjusted_elapsed < FinalAll_time:
            brightness_factor = max_brightness_factor
            accent = any(start <= adjusted_elapsed < stop for (start, stop) in back_vocals_phase7)
            update_fast_spiral_phase7(spiral_offset, brightness_factor, accent)
            spiral_offset += fast_spiral_speed2
        elif adjusted_elapsed < FadeOut_time:
            update_final_spiral(spiral_offset, final_brightness, final_spiral_speed)
            spiral_offset += final_spiral_speed
        elif adjusted_elapsed < End_time:
            fade_progress = (adjusted_elapsed - FadeOut_time) / (End_time - FadeOut_time)
            update_final_fadeout(spiral_offset, final_brightness, fade_progress)
            spiral_offset += final_spiral_speed * (1 - fade_progress)
        else:
            break

        time.sleep(0.05)

    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

# ====================================================
# Flask Web Application (Mobile-Friendly UI)
# ====================================================
app = Flask(__name__)
led_thread = None

@app.route('/')
def index():
    html = """
    <!doctype html>
    <html>
      <head>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>LED Light Show Synchronized to Song</title>
        <style>
          body { font-family: Arial, sans-serif; text-align: center; margin: 0; padding: 20px; background-color: #f0f0f0; }
          h1 { font-size: 1.8em; margin-top: 10px; color: #333; }
          button { padding: 15px 25px; font-size: 1.2em; border: none; border-radius: 5px; background-color: #4CAF50; color: white; margin-top: 20px; width: 80%; max-width: 300px; }
          button:active { background-color: #45a049; }
          audio { width: 90%; max-width: 400px; margin-top: 20px; }
        </style>
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
