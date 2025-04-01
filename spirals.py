import time
import math
import pandas as pd
import colorsys
from rpi_ws281x import PixelStrip, Color

def animate_spirals(csv_file, duration=30, interval=0.05, spiral_factor=4*math.pi, speed=2.0):
    """
    Animate full-tree colored spirals on a 3D LED tree.

    Each LED’s color is determined from its position in cylindrical coordinates.
    The angular position (theta) plus a twist based on its normalized height and a time-dependent offset
    produces a phase that is mapped to a hue (using the HSV color model). The spirals rotate continuously,
    filling the entire tree with a dynamic, colorful pattern.

    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Total duration (in seconds) for the animation.
      interval (float): Time (in seconds) between animation frames.
      spiral_factor (float): Total twist in radians across the tree’s height.
                              (e.g., 4π means two full twists from bottom to top)
      speed (float): Angular speed (radians per second) of the spiral rotation.
    """
    # Load LED coordinates; assume CSV rows correspond to physical LED order.
    df = pd.read_csv(csv_file)
    df['led_index'] = df.index

    # LED strip configuration.
    LED_COUNT      = len(df)
    LED_PIN        = 18            # GPIO pin (data signal)
    LED_FREQ_HZ    = 800000        # LED signal frequency in hertz
    LED_DMA        = 10            # DMA channel to use for generating signal
    LED_BRIGHTNESS = 125           # Brightness (0 to 255)
    LED_INVERT     = False         # True to invert the signal (if needed)
    LED_CHANNEL    = 0             # Set to 0 for GPIO 18

    # Initialize the LED strip.
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                       LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    # Determine the tree’s bounds and compute the center for X and Y.
    tree_x_min, tree_x_max = df['X'].min(), df['X'].max()
    tree_y_min, tree_y_max = df['Y'].min(), df['Y'].max()
    tree_z_min, tree_z_max = df['Z'].min(), df['Z'].max()

    x_center = (tree_x_min + tree_x_max) / 2.0
    y_center = (tree_y_min + tree_y_max) / 2.0

    # Main animation loop.
    start_time = time.time()
    while time.time() - start_time < duration:
        t = time.time() - start_time
        # Process each LED.
        for _, row in df.iterrows():
            idx = int(row['led_index'])
            x, y, z = row['X'], row['Y'], row['Z']
            # Convert (x, y) to polar coordinates relative to the tree center.
            theta = math.atan2(y - y_center, x - x_center)  # angle in radians
            # Normalize z (height) to range 0..1.
            norm_z = (z - tree_z_min) / (tree_z_max - tree_z_min) if tree_z_max > tree_z_min else 0

            # Compute a phase that produces the spiral pattern.
            phase = theta + norm_z * spiral_factor + speed * t
            # Map the phase to a hue value in the range [0, 1].
            hue = (phase % (2 * math.pi)) / (2 * math.pi)
            # Convert HSV to RGB (with full saturation and brightness).
            r_float, g_float, b_float = colorsys.hsv_to_rgb(hue, 1, 1)
            r = int(r_float * 255)
            g = int(g_float * 255)
            b = int(b_float * 255)
            strip.setPixelColor(idx, Color(r, g, b))
        strip.show()
        time.sleep(interval)

    # Turn off all LEDs when the animation ends.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Replace 'coordinates.csv' with the path to your LED coordinates file if necessary.
    animate_spirals('coordinates.csv', duration=30, interval=0.05, spiral_factor=4*math.pi, speed=2.0)
