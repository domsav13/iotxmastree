import time
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def animate_leds(csv_file, interval=0.2, duration=30):
    """
    Animate the LED strip by lighting LEDs from the bottom to the top and then reversing the order.

    Parameters:
      csv_file (str): Path to the CSV file with LED coordinates (columns: X, Y, Z)
      interval (float): Time in seconds between LED updates.
      duration (float): Total duration in seconds for the animation.
    """
    # Load LED coordinates from CSV
    df = pd.read_csv(csv_file)
    # Add a column for physical LED index (assumes CSV row order matches the physical order)
    df['led_index'] = df.index

    # Sort LEDs by the Z coordinate (lowest Z at the bottom)
    df_sorted = df.sort_values('Z').reset_index(drop=True)
    # Extract the physical LED indices in sorted order
    sorted_led_indices = df_sorted['led_index'].tolist()

    # LED strip configuration:
    LED_COUNT      = len(df)       # Total number of LEDs
    LED_PIN        = 18            # GPIO pin connected to the data signal (must support PWM)
    LED_FREQ_HZ    = 800000        # LED signal frequency in hertz (usually 800kHz)
    LED_DMA        = 10            # DMA channel to use for generating signal
    LED_BRIGHTNESS = 255           # Brightness (0 to 255)
    LED_INVERT     = False         # True to invert the signal (when using NPN transistor level shift)
    LED_CHANNEL    = 0             # Set to 0 for GPIO 18

    # Create PixelStrip object with the configuration.
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    # Build a sequence: go from bottom to top, then reverse (excluding the top LED to avoid duplicate)
    sequence = sorted_led_indices + sorted_led_indices[-2::-1]

    start_time = time.time()
    seq_idx = 0

    while time.time() - start_time < duration:
        # Get the physical LED index to light up next.
        current_led = sequence[seq_idx % len(sequence)]

        # Turn off all LEDs first.
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))

        # Light the current LED in red.
        strip.setPixelColor(current_led, Color(255, 0, 0))
        strip.show()

        time.sleep(interval)
        seq_idx += 1

if __name__ == '__main__':
    animate_leds('/mnt/data/coordinates.csv', interval=0.2, duration=30)
