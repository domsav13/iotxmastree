import time
import random
import math
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def animate_fireworks(csv_file, duration=30, interval=0.05,
                      firework_interval_range=(1, 3), firework_duration=1.0):
    """
    Animate random firework effects on a 3D LED tree.

    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Total duration (in seconds) for the entire animation.
      interval (float): Time (in seconds) between animation frames.
      firework_interval_range (tuple): Range (in seconds) for random delay between fireworks.
      firework_duration (float): Duration (in seconds) for each firework effect.
    """
    # Load LED coordinates; assume CSV rows correspond to physical LED order.
    df = pd.read_csv(csv_file)
    df['led_index'] = df.index

    # LED strip configuration:
    LED_COUNT      = len(df)       # Total number of LEDs
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

    # Get tree bounds from the coordinates (to determine a local region for fireworks).
    tree_x_min, tree_x_max = df['X'].min(), df['X'].max()
    tree_y_min, tree_y_max = df['Y'].min(), df['Y'].max()
    tree_z_min, tree_z_max = df['Z'].min(), df['Z'].max()
    max_dim = max(tree_x_max - tree_x_min,
                  tree_y_max - tree_y_min,
                  tree_z_max - tree_z_min)
    # Use 10% of the maximum dimension as the radius for a localized firework effect.
    local_radius = 0.1 * max_dim

    # Define firework colors as (R, G, B) tuples: orange, red, and yellow.
    firework_colors = [(255, 69, 0), (255, 0, 0), (255, 255, 0)]

    start_time = time.time()
    while time.time() - start_time < duration:
        # Clear all LEDs.
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))
        strip.show()

        # Wait a random interval before the next firework.
        sleep_time = random.uniform(firework_interval_range[0], firework_interval_range[1])
        time.sleep(sleep_time)

        # Pick a random LED as the center of the firework.
        center_row = df.sample(n=1).iloc[0]
        center_x, center_y, center_z = center_row['X'], center_row['Y'], center_row['Z']

        # Find all LEDs within the local_radius of the chosen center.
        local_leds = []
        for _, row in df.iterrows():
            dx = row['X'] - center_x
            dy = row['Y'] - center_y
            dz = row['Z'] - center_z
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            if distance <= local_radius:
                local_leds.append(int(row['led_index']))
        # If none are found, use the center LED itself.
        if not local_leds:
            local_leds = [int(center_row['led_index'])]

        # Choose one firework color.
        r0, g0, b0 = random.choice(firework_colors)

        # Firework explosion: first, an immediate burst.
        for idx in local_leds:
            strip.setPixelColor(idx, Color(r0, g0, b0))
        strip.show()

        # Fade-out effect over the firework_duration.
        firework_steps = int(firework_duration / interval)
        for step in range(firework_steps):
            fade = 1.0 - (step / firework_steps)
            for idx in local_leds:
                r = int(r0 * fade)
                g = int(g0 * fade)
                b = int(b0 * fade)
                strip.setPixelColor(idx, Color(r, g, b))
            strip.show()
            time.sleep(interval)

        # Clear the local LEDs after the firework.
        for idx in local_leds:
            strip.setPixelColor(idx, Color(0, 0, 0))
        strip.show()

    # Turn off all LEDs when the animation ends.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Change 'coordinates.csv' to the path of your CSV file if needed.
    animate_fireworks('coordinates.csv', duration=30, interval=0.05,
                      firework_interval_range=(1, 3), firework_duration=1.0)
