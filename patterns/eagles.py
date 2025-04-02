import time
import math
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def lerp_color(c1, c2, t):
    """
    Linearly interpolate between two colors (R, G, B) using factor t in [0,1].
    """
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return (r, g, b)

def get_eagles_color(t):
    """
    Given a parameter t in [0,1], interpolate through the Eagles palette.
    
    The palette consists of:
      - Midnight Green: (0, 76, 84)
      - Silver:         (165, 172, 175)
      - Black:          (0, 0, 0)
      - White:          (255, 255, 255)
    
    The gradient is segmented equally.
    """
    palette = [
        (0, 76, 84),      # Midnight Green
        (165, 172, 175),  # Silver
        (0, 0, 0),        # Black
        (255, 255, 255)   # White
    ]
    # There are 3 segments.
    if t < 0.33:
        # Interpolate between palette[0] and palette[1]
        t2 = t / 0.33
        return lerp_color(palette[0], palette[1], t2)
    elif t < 0.66:
        t2 = (t - 0.33) / 0.33
        return lerp_color(palette[1], palette[2], t2)
    else:
        t2 = (t - 0.66) / 0.34
        return lerp_color(palette[2], palette[3], t2)

def animate_eagles(csv_file, duration=30, interval=0.05, speed=0.2):
    """
    Animate an LED display using a moving gradient based on Philadelphia Eagles colors.
    
    Each LED's color is computed from a phase value derived from its index and a time-based offset.
    The phase is used to extract a color from the Eagles palette.
    
    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Animation duration in seconds.
      interval (float): Delay between LED updates (seconds).
      speed (float): Speed at which the color wave moves.
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

    start_time = time.time()
    while time.time() - start_time < duration:
        t = time.time() - start_time
        # For each LED, compute a phase that cycles over time.
        for idx, row in df.iterrows():
            # Base phase determined by LED index.
            base_phase = idx / LED_COUNT
            # Add a time component; speed controls the wave motion.
            phase = (base_phase + t * speed) % 1.0
            # Get the color from our Eagles palette.
            color_tuple = get_eagles_color(phase)
            strip.setPixelColor(int(row['led_index']), Color(*color_tuple))
        strip.show()
        time.sleep(interval)

    # Turn off all LEDs when finished.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Replace 'coordinates.csv' with your LED coordinate CSV file if needed.
    animate_eagles('coordinates.csv', duration=30, interval=0.05, speed=0.2)
