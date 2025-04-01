import time
import math
import numpy as np
import pandas as pd
import colorsys
from pydub import AudioSegment
from pydub.playback import play
from threading import Thread
from rpi_ws281x import PixelStrip, Color

def animate_music_sync(csv_file, mp3_file, chunk_size=1024, interval=0.05, led_scale=10.0):
    """
    Animate LED colors synced to an MP3 file's frequency spectrum while playing the song in real time.

    The MP3 file is loaded and processed in real time. For each time interval, a chunk of audio samples
    corresponding to the elapsed playback time is extracted, and its FFT is computed. The frequency spectrum
    is divided into bands (one or more per LED), and each LED's brightness is modulated based on its band's amplitude.
    The LED's color is determined by mapping its index to a hue (producing a gradient effect).

    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      mp3_file (str): Path to the MP3 file.
      chunk_size (int): Number of audio samples per FFT (e.g., 1024).
      interval (float): Delay (in seconds) between LED update frames.
      led_scale (float): Scaling factor to convert FFT magnitude to a brightness value (0.0–1.0).
    """
    # Load LED coordinates.
    df = pd.read_csv(csv_file)
    df['led_index'] = df.index
    LED_COUNT = len(df)

    # LED strip configuration.
    LED_PIN        = 18           # GPIO pin (data signal)
    LED_FREQ_HZ    = 800000       # LED signal frequency in hertz
    LED_DMA        = 10           # DMA channel to use for generating signal
    LED_BRIGHTNESS = 125          # Brightness (0 to 255)
    LED_INVERT     = False        # True to invert the signal (if needed)
    LED_CHANNEL    = 0            # Set to 0 for GPIO 18
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                       LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    # Load the MP3 file.
    song = AudioSegment.from_mp3(mp3_file)
    # Convert to a numpy array of samples.
    samples = np.array(song.get_array_of_samples())
    if song.channels > 1:
        samples = samples.reshape((-1, song.channels))
        samples = samples[:, 0]  # Use the first channel if stereo.
    # Normalize samples to float32 in range [-1, 1].
    samples = samples.astype(np.float32) / (2**15)
    sample_rate = song.frame_rate
    total_samples = len(samples)
    
    # Determine FFT bins per LED.
    fft_bins = chunk_size // 2
    bins_per_led = max(1, fft_bins // LED_COUNT)

    # Function to play the song in a separate thread.
    def play_song(audio):
        play(audio)

    # Start the song playback in a background thread.
    song_thread = Thread(target=play_song, args=(song,))
    song_thread.start()

    # Record the start time to synchronize audio processing with playback.
    start_time = time.time()

    # Process audio in real time.
    while True:
        elapsed = time.time() - start_time
        # Calculate the current sample index based on elapsed time.
        current_sample = int(elapsed * sample_rate)
        if current_sample + chunk_size > total_samples:
            break  # End loop when song samples are exhausted.

        # Extract a chunk of audio.
        chunk = samples[current_sample: current_sample + chunk_size]
        # Apply a Hanning window.
        window = np.hanning(len(chunk))
        windowed = chunk * window

        # Compute the FFT and its magnitude.
        fft_result = np.fft.rfft(windowed)
        magnitude = np.abs(fft_result)

        # Update each LED based on its corresponding frequency band.
        for led in range(LED_COUNT):
            start_bin = led * bins_per_led
            end_bin = start_bin + bins_per_led
            band_mag = np.mean(magnitude[start_bin:end_bin])
            # Scale the magnitude to a brightness value (clamped to 1.0).
            brightness = min(band_mag * led_scale, 1.0)
            # Map LED index to a hue (e.g., from red to blue).
            hue = (led / LED_COUNT) * 0.66  # 0.0 = red, 0.66 = blue
            r_float, g_float, b_float = colorsys.hsv_to_rgb(hue, 1, brightness)
            r = int(r_float * 255)
            g = int(g_float * 255)
            b = int(b_float * 255)
            strip.setPixelColor(led, Color(r, g, b))
        strip.show()
        time.sleep(interval)

    # Turn off all LEDs after the song ends.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
    song_thread.join()

if __name__ == '__main__':
    # Replace 'coordinates.csv' and 'song.mp3' with your file paths if needed.
    animate_music_sync('coordinates.csv', 'song.mp3', chunk_size=1024, interval=0.05, led_scale=10.0)
