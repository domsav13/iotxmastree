import time
import math
import random
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def lerp_color(c1, c2, t):
    """
    Linearly interpolate between two colors c1 and c2.
    c1, c2: (R, G, B) tuples.
    t: Interpolation factor between 0 and 1.
    Returns: (R, G, B) tuple.
    """
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return (r, g, b)

def animate_ripple(csv_file, duration=30, interval=0.05, ripple_speed=1.0, ripple_width=0.3,
                   gradient_start=(255, 0, 0), gradient_end=(255, 255, 0)):
    """
    Animate a ripple effect with a color gradient on a 3D LED tree.
    
    A ripple emanates from a randomly chosen center LED and expands outward.
    LEDs whose 3D distance from the center falls within a narrow band (ripple_width)
    around the ripple front are lit with a color that is a linear blend between
    gradient_start and gradient_end.
    
    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Total duration (in seconds) for the animation.
      interval (float): Time (in seconds) between animation frames.
      ripple_speed (float): Speed at which the ripple expands (in same units as the coordinates).
      ripple_width (float): Thickness of the ripple band.
      gradient_start (tuple): RGB tuple for one end of the gradient.
      gradient_end (tuple): RGB tuple for the other end of the gradient.
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

    # Start animation.
    animation_start = time.time()
    # Initialize a new ripple cycle.
    current_center_row = df.sample(n=1).iloc[0]
    center = (current_center_row['X'], current_center_row['Y'], current_center_row['Z'])
    ripple_start_time = time.time()
    
    # Precompute distances from the current ripple center.
    distances = []
    for _, row in df.iterrows():
        dx = row['X'] - center[0]
        dy = row['Y'] - center[1]
        dz = row['Z'] - center[2]
        distances.append(math.sqrt(dx*dx + dy*dy + dz*dz))
    max_distance = max(distances)

    while time.time() - animation_start < duration:
        current_time = time.time()
        elapsed = current_time - ripple_start_time
        ripple_radius = ripple_speed * elapsed

        # If the ripple has expanded past the furthest LED, start a new ripple.
        if ripple_radius > max_distance:
            current_center_row = df.sample(n=1).iloc[0]
            center = (current_center_row['X'], current_center_row['Y'], current_center_row['Z'])
            ripple_start_time = current_time
            distances = []
            for _, row in df.iterrows():
                dx = row['X'] - center[0]
                dy = row['Y'] - center[1]
                dz = row['Z'] - center[2]
                distances.append(math.sqrt(dx*dx + dy*dy + dz*dz))
            max_distance = max(distances)
            ripple_radius = 0

        # Update each LED based on its distance from the ripple front.
        for idx, d in enumerate(distances):
            diff = d - ripple_radius
            # If the LED is within the ripple band, compute its gradient color.
            if abs(diff) <= ripple_width / 2:
                # Map diff from [-ripple_width/2, +ripple_width/2] to [0, 1].
                normalized = (diff + (ripple_width / 2)) / ripple_width
                color = lerp_color(gradient_start, gradient_end, normalized)
            else:
                color = (0, 0, 0)
            strip.setPixelColor(idx, Color(*color))
        strip.show()
        time.sleep(interval)

    # Turn off all LEDs when finished.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Adjust the CSV file path and parameters as needed.
    animate_ripple('coordinates.csv', duration=30, interval=0.05, ripple_speed=1.0,
                   ripple_width=0.3, gradient_start=(255, 0, 0), gradient_end=(255, 255, 0))
