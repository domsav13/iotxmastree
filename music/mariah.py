#!/usr/bin/env python3
import os
from flask import Flask, send_from_directory, render_template_string, jsonify
from threading import Thread
import time
import numpy as np
import pandas as pd
import colorsys
from rpi_ws281x import PixelStrip, Color
from pydub import AudioSegment
from io import BytesIO

app = Flask(__name__)
led_thread = None

def animate_music_sync_rich(csv_file, mp3_file, chunk_size=1024, interval=0.05, led_scale=10.0, global_scale=3.0):
    """
    Enhanced LED animation synchronized with music using both amplitude and refined frequency data.
    """
    # Define total number of LEDs on your tree.
    TOTAL_LED_COUNT = 150  # Adjust this to match your hardware setup.
    LED_COUNT = TOTAL_LED_COUNT

    # Optionally try to load LED coordinates from CSV for ordering.
    try:
        df = pd.read_csv(csv_file)
        if len(df) < TOTAL_LED_COUNT:
            print("Warning: CSV file contains fewer rows than total LED count. Using default positions for missing LEDs.")
    except Exception as e:
        print("Could not load CSV file, using default LED count.")
        df = pd.DataFrame({'X': [0]*TOTAL_LED_COUNT, 'Y': [0]*TOTAL_LED_COUNT, 'Z': [0]*TOTAL_LED_COUNT})

    # LED strip configuration.
    LED_PIN        = 18
    LED_FREQ_HZ    = 800000
    LED_DMA        = 10
    LED_BRIGHTNESS = 125
    LED_INVERT     = False
    LED_CHANNEL    = 0
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    
    # Load the MP3 file entirely into memory.
    with open(mp3_file, 'rb') as f:
        mp3_data = f.read()
    try:
        song = AudioSegment.from_file(BytesIO(mp3_data), format="mp3")
    except Exception as e:
        print("Error loading MP3 file:", e)
        return
    
    # Prepare audio samples.
    samples = np.array(song.get_array_of_samples())
    if song.channels > 1:
        samples = samples.reshape((-1, song.channels))
        samples = samples[:, 0]  # Use the first channel if stereo.
    samples = samples.astype(np.float32) / (2**15)  # Normalize to [-1,1]
    sample_rate = song.frame_rate
    total_samples = len(samples)
    
    # Pre-calculate FFT frequency bins.
    frequencies = np.fft.rfftfreq(chunk_size, d=1.0/sample_rate)
    
    # Compute logarithmically spaced frequency boundaries (from 20 Hz to Nyquist).
    f_min = 20
    f_max = sample_rate / 2.0
    freq_boundaries = np.logspace(np.log10(f_min), np.log10(f_max), LED_COUNT + 1)
    
    # Prepare smoothing state for each LED.
    prev_brightness = np.zeros(LED_COUNT)
    smoothing_factor = 0.3  # Lower values mean faster response (more bounce), higher values add persistence.
    
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        current_sample = int(elapsed * sample_rate)
        if current_sample + chunk_size > total_samples:
            break
        
        # Get the current chunk and compute its RMS amplitude.
        chunk = samples[current_sample: current_sample + chunk_size]
        rms = np.sqrt(np.mean(chunk**2))
        
        # Compute FFT to get frequency data.
        window = np.hanning(len(chunk))
        windowed = chunk * window
        fft_result = np.fft.rfft(windowed)
        magnitude = np.abs(fft_result)
        
        # Derive a global hue offset from the dominant frequency in the chunk.
        dominant_idx = np.argmax(magnitude)
        dominant_norm = dominant_idx / (len(magnitude) - 1)  # Normalized value between 0 and 1.
        hue_offset = dominant_norm * 0.66  # Scale to a hue range (red to blue).
        
        # Update each LED.
        for led in range(LED_COUNT):
            # Determine frequency band for this LED using logarithmic boundaries.
            lower_bound = freq_boundaries[led]
            upper_bound = freq_boundaries[led+1]
            # Find FFT bin indices in this frequency band.
            indices = np.where((frequencies >= lower_bound) & (frequencies < upper_bound))[0]
            if len(indices) > 0:
                band_mag = np.mean(magnitude[indices])
            else:
                band_mag = 0
            
            # Blend local frequency magnitude and overall amplitude.
            brightness_val = np.clip(np.tanh((band_mag * led_scale) + (rms * global_scale)), 0, 1)
            
            # Smooth the brightness for a more fluid effect.
            brightness_val = (smoothing_factor * prev_brightness[led] + 
                              (1 - smoothing_factor) * brightness_val)
            prev_brightness[led] = brightness_val
            
            # Calculate a base hue from the LED's index.
            base_hue = (led / LED_COUNT) * 0.66
            # Add dynamic hue offset and a slight boost from the brightness.
            hue = (base_hue + hue_offset + 0.1 * brightness_val) % 1.0
            
            # Convert HSV to RGB.
            r_float, g_float, b_float = colorsys.hsv_to_rgb(hue, 1, brightness_val)
            r_val = int(r_float * 255)
            g_val = int(g_float * 255)
            b_val = int(b_float * 255)
            strip.setPixelColor(led, Color(r_val, g_val, b_val))
        strip.show()
        time.sleep(interval)
    
    # Turn off all LEDs when finished.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

@app.route('/')
def index():
    html = """
    <!doctype html>
    <html>
      <head>
        <title>Enhanced LED Music Sync</title>
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
        <h1>Enhanced LED Music Sync</h1>
        <button onclick="startShow()">Start Light Show</button>
        <br><br>
        <audio id="audio" controls>
          <source src="/audio/mariah.mp3" type="audio/mpeg">
          Your browser does not support the audio element.
        </audio>
        <p>Enjoy the synchronized LED light show with music!</p>
      </body>
    </html>
    """
    return render_template_string(html)

@app.route('/start', methods=['POST'])
def start():
    global led_thread
    if led_thread is None or not led_thread.is_alive():
        led_thread = Thread(target=animate_music_sync_rich,
                            args=('coordinates.csv', 'audio/mariah.mp3', 1024, 0.05, 10.0, 3.0))
        led_thread.daemon = True
        led_thread.start()
        return jsonify({"status": "Enhanced light show started"})
    else:
        return jsonify({"status": "Light show already running"})

@app.route('/audio/<path:filename>')
def audio(filename):
    return send_from_directory('audio', filename)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
