import time
import random
import math
import pandas as pd
import colorsys
from rpi_ws281x import PixelStrip, Color

def animate_comet_paths(csv_file, duration=30, interval=0.05, num_comets=5, speed=5, trail_threshold=1.0):
    """
    Animate a comet effect on a 3D LED tree.
    
    Multiple comets spawn at the top of the tree (z = maximum) with vibrant colors.
    They fall downward, leaving behind a fading trail that lights up nearby LEDs.
    When a comet falls below the tree, it is respawned at the top with a new random color.
    
    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Total duration of the animation in seconds.
      interval (float): Delay between animation frames in seconds.
      num_comets (int): Number of concurrent comets.
      speed (float): Falling speed (in coordinate units per second).
      trail_threshold (float): Maximum distance for a comet’s color influence.
    """
    # Load LED coordinates from CSV.
    df = pd.read_csv(csv_file)
    df['led_index'] = df.index
    LED_COUNT = len(df)
    
    # LED strip configuration.
    LED_PIN        = 18       # GPIO pin for data signal
    LED_FREQ_HZ    = 800000   # LED signal frequency in hertz
    LED_DMA        = 10       # DMA channel to use
    LED_BRIGHTNESS = 125      # Initial brightness
    LED_INVERT     = False    # Invert signal if needed
    LED_CHANNEL    = 0        # Use channel 0 for GPIO 18

    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                       LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    # Determine tree bounds from the CSV.
    tree_x_min, tree_x_max = df['X'].min(), df['X'].max()
    tree_y_min, tree_y_max = df['Y'].min(), df['Y'].max()
    tree_z_min, tree_z_max = df['Z'].min(), df['Z'].max()

    # Initialize comets at the top of the tree.
    comets = []
    for _ in range(num_comets):
        comet = {
            'x': random.uniform(tree_x_min, tree_x_max),
            'y': random.uniform(tree_y_min, tree_y_max),
            'z': tree_z_max,
        }
        # Choose a vibrant color using HSV (full saturation and brightness).
        hue = random.random()
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        comet['color'] = (int(r * 255), int(g * 255), int(b * 255))
        comets.append(comet)

    animation_start = time.time()
    prev_time = animation_start

    while time.time() - animation_start < duration:
        # --- Draw Phase ---
        # Clear all LEDs to a dark background.
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))
        
        # For each LED, compute the color contribution from each comet.
        for idx, row in df.iterrows():
            led_x, led_y, led_z = row['X'], row['Y'], row['Z']
            r_sum, g_sum, b_sum = 0, 0, 0  # Start with black
            for comet in comets:
                dx = led_x - comet['x']
                dy = led_y - comet['y']
                dz = led_z - comet['z']
                distance = math.sqrt(dx * dx + dy * dy + dz * dz)
                if distance <= trail_threshold:
                    # The closer the LED is to the comet, the stronger the effect.
                    factor = 1 - (distance / trail_threshold)
                    r_sum += comet['color'][0] * factor
                    g_sum += comet['color'][1] * factor
                    b_sum += comet['color'][2] * factor
            # Clamp the color values to a maximum of 255.
            r_final = min(int(r_sum), 255)
            g_final = min(int(g_sum), 255)
            b_final = min(int(b_sum), 255)
            if r_final or g_final or b_final:
                strip.setPixelColor(int(row['led_index']), Color(r_final, g_final, b_final))
        
        strip.show()
        time.sleep(interval)
        
        # --- Update Phase ---
        current_time = time.time()
        dt = current_time - prev_time
        prev_time = current_time

        # Update each comet's position by moving it downward.
        for comet in comets:
            comet['z'] -= speed * dt
            # Optional: add a slight horizontal drift.
            # comet['x'] += random.uniform(-0.005, 0.005) * dt
            # comet['y'] += random.uniform(-0.005, 0.005) * dt

            # If the comet has fallen below the tree, respawn it at the top with a new color.
            if comet['z'] < tree_z_min:
                comet['x'] = random.uniform(tree_x_min, tree_x_max)
                comet['y'] = random.uniform(tree_y_min, tree_y_max)
                comet['z'] = tree_z_max
                hue = random.random()
                r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
                comet['color'] = (int(r * 255), int(g * 255), int(b * 255))

    # Turn off all LEDs when the animation ends.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Adjust 'coordinates.csv' to match your LED coordinate file location if needed.
    animate_comet_paths('coordinates.csv', duration=30, interval=0.05,
                         num_comets=5, speed=5, trail_threshold=1.0)
