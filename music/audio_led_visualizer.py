#!/usr/bin/env python3
import os
from flask import Flask, send_from_directory, render_template_string
from threading import Thread
import time
import math
import numpy as np
import pandas as pd
import colorsys
from rpi_ws281x import PixelStrip, Color
from pydub import AudioSegment
from pydub.playback import play
from io import BytesIO

# Optional: If necessary, explicitly set the ffmpeg binary path.
# os.environ["FFMPEG_BINARY"] = "/usr/bin/ffmpeg"

def animate_music_sync(csv_file, mp3_file, chunk_size=1024, interval=0.05, led_scale=10.0):
    """
    Animate LED colors synced to an MP3 file's frequency spectrum while playing the song.
    
    The MP3 file is loaded entirely into memory via BytesIO so that ffmpeg can seek properly.
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
    
    # Record start time for synchronization.
    start_time = time.time()
    
    # Optionally, play the song locally in a background thread.
    song_thread = Thread(target=play, args=(song,))
    song_thread.daemon = True
    song_thread.start()
    
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
            # Map LED index to a hue (creating a red-to-blue gradient).
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

# Define Flask app.
app = Flask(__name__)

@app.route('/')
def index():
    # Simple web page with an audio player.
    html = """
    <!doctype html>
    <html>
      <head>
        <title>LED Music Sync</title>
      </head>
      <body>
        <h1>LED Music Sync</h1>
        <audio controls autoplay>
          <source src="/audio/song.mp3" type="audio/mpeg">
          Your browser does not support the audio element.
        </audio>
        <p>Enjoy the synchronized LED show!</p>
      </body>
    </html>
    """
    return render_template_string(html)

@app.route('/audio/<path:filename>')
def audio(filename):
    # Serve audio files from the "audio" directory.
    return send_from_directory('audio', filename)

if __name__ == '__main__':
    # Start the LED animation in a separate thread.
    led_thread = Thread(target=animate_music_sync, args=('coordinates.csv', 'audio/song.mp3', 1024, 0.05, 10.0))
    led_thread.daemon = True
    led_thread.start()
    
    # Run the Flask server so that clients can play the song over the web.
    app.run(host='0.0.0.0', port=5000)
