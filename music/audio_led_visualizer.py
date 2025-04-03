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

# Global variable to keep track of the LED animation thread.
led_thread = None

def animate_music_sync(csv_file, mp3_file, chunk_size=1024, interval=0.05, led_scale=10.0):
    """
    Animate LED colors synced to an MP3 file's frequency spectrum.
    This function loads the MP3 for analysis but does not play it locally.
    It uses the system time (set at start) to drive the LED updates.
    """
    # Load LED coordinates.
    df = pd.read_csv(csv_file)
    df['led_index'] = df.index
    LED_COUNT = len(df)
    
    # LED strip configuration.
    LED_PIN        = 18            # GPIO pin (data signal)
    LED_FREQ_HZ    = 800000        # LED signal frequency in hertz
    LED_DMA        = 10            # DMA channel for signal generation
    LED_BRIGHTNESS = 125           # Brightness (0 to 255)
    LED_INVERT     = False         # Invert signal if needed
    LED_CHANNEL    = 0             # Set to 0 for GPIO 18
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                       LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    
    # Load the MP3 file entirely into memory.
    with open(mp3_file, 'rb') as f:
        mp3_data = f.read()
    try:
        song = AudioSegment.from_file(BytesIO(mp3_data), format="mp3")
    except Exception as e:
        print("Error loading MP3 file:", e)
        return
    
    # Convert to a numpy array of samples.
    samples = np.array(song.get_array_of_samples())
    if song.channels > 1:
        samples = samples.reshape((-1, song.channels))
        samples = samples[:, 0]  # Use first channel if stereo.
    samples = samples.astype(np.float32) / (2**15)  # Normalize to [-1,1]
    sample_rate = song.frame_rate
    total_samples = len(samples)
    
    # Determine FFT bins per LED.
    fft_bins = chunk_size // 2
    bins_per_led = max(1, fft_bins // LED_COUNT)
    
    # Use the current time as the start time for synchronization.
    start_time = time.time()
    
    while True:
        elapsed = time.time() - start_time
        current_sample = int(elapsed * sample_rate)
        if current_sample + chunk_size > total_samples:
            break  # End loop when song is finished.
        
        # Process a chunk of audio.
        chunk = samples[current_sample: current_sample + chunk_size]
        window = np.hanning(len(chunk))
        windowed = chunk * window
        fft_result = np.fft.rfft(windowed)
        magnitude = np.abs(fft_result)
        
        # Update each LED based on its corresponding frequency band.
        for led in range(LED_COUNT):
            start_bin = led * bins_per_led
            end_bin = start_bin + bins_per_led
            band_mag = np.mean(magnitude[start_bin:end_bin])
            brightness = min(band_mag * led_scale, 1.0)
            # Map LED index to a hue (red-to-blue gradient).
            hue = (led / LED_COUNT) * 0.66  # 0.0 = red, 0.66 = blue.
            r_float, g_float, b_float = colorsys.hsv_to_rgb(hue, 1, brightness)
            r = int(r_float * 255)
            g = int(g_float * 255)
            b = int(b_float * 255)
            strip.setPixelColor(led, Color(r, g, b))
        strip.show()
        time.sleep(interval)
    
    # Turn off all LEDs after playback.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

@app.route('/')
def index():
    html = """
    <!doctype html>
    <html>
      <head>
        <title>LED Music Sync</title>
        <script>
          function startShow() {
            fetch('/start', {method: 'POST'})
              .then(response => response.json())
              .then(data => {
                console.log(data);
                // Start playing audio when the light show is triggered.
                var audio = document.getElementById('audio');
                audio.play();
              })
              .catch(err => console.error(err));
          }
        </script>
      </head>
      <body>
        <h1>LED Music Sync</h1>
        <button onclick="startShow()">Start Light Show</button>
        <br><br>
        <audio id="audio" controls>
          <source src="/audio/mariah.mp3" type="audio/mpeg">
          Your browser does not support the audio element.
        </audio>
        <p>Enjoy the synchronized LED show!</p>
      </body>
    </html>
    """
    return render_template_string(html)

@app.route('/start', methods=['POST'])
def start():
    global led_thread
    if led_thread is None or not led_thread.is_alive():
        led_thread = Thread(target=animate_music_sync,
                            args=('coordinates.csv', 'audio/mariah.mp3', 1024, 0.05, 10.0))
        led_thread.daemon = True
        led_thread.start()
        return jsonify({"status": "Light show started"})
    else:
        return jsonify({"status": "Light show already running"})

@app.route('/audio/<path:filename>')
def audio(filename):
    return send_from_directory('audio', filename)

if __name__ == '__main__':
    # Run the Flask server so clients can trigger the show and play audio.
    app.run(host='0.0.0.0', port=5000)
