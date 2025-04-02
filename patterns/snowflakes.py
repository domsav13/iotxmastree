import time
import random
import math
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def animate_snowflake_paths(csv_file, duration=30, interval=0.05,
                            num_snowflakes=5, speed=0.1, threshold=1.0):
    """
    Animate white snowflake paths on a 3D LED tree.
    
    Snowflakes spawn at the top of the tree (LEDs with the highest Z values) and fall downward.
    As a snowflake passes near an LED (within the specified threshold distance), that LED is lit white.
    Multiple snowflake paths occur concurrently.
    
    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Total duration of the animation in seconds.
      interval (float): Delay between animation frames in seconds.
      num_snowflakes (int): Number of falling snowflakes (paths) to simulate.
      speed (float): Falling speed (in coordinate units per second).
      threshold (float): Distance threshold for lighting an LED.
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

    # Determine tree bounds from the CSV.
    tree_x_min, tree_x_max = df['X'].min(), df['X'].max()
    tree_y_min, tree_y_max = df['Y'].min(), df['Y'].max()
    tree_z_min, tree_z_max = df['Z'].min(), df['Z'].max()

    # Identify the top LED (with maximum Z).
    top_led_row = df.loc[df['Z'].idxmax()]

    # Initialize snowflake particles.
    # Force one snowflake to spawn exactly at the top LED's position.
    snowflakes = []
    first_snowflake = {
        'x': top_led_row['X'],
        'y': top_led_row['Y'],
        'z': tree_z_max
    }
    snowflakes.append(first_snowflake)
    # The rest spawn randomly across the top.
    for _ in range(num_snowflakes - 1):
        snowflake = {
            'x': random.uniform(tree_x_min, tree_x_max),
            'y': random.uniform(tree_y_min, tree_y_max),
            'z': tree_z_max
        }
        snowflakes.append(snowflake)

    animation_start = time.time()
    prev_time = animation_start

    while time.time() - animation_start < duration:
        # --- Draw Phase ---
        # Clear all LEDs.
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))

        # For each LED, light it white if any snowflake is close enough.
        for idx, row in df.iterrows():
            led_x, led_y, led_z = row['X'], row['Y'], row['Z']
            for sf in snowflakes:
                dx = led_x - sf['x']
                dy = led_y - sf['y']
                dz = led_z - sf['z']
                distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                if distance <= threshold:
                    strip.setPixelColor(int(row['led_index']), Color(255, 255, 255))
                    break  # Only one snowflake needed to light the LED.
        strip.show()
        time.sleep(interval)

        # --- Update Phase ---
        current_time = time.time()
        dt = current_time - prev_time
        prev_time = current_time

        # Update each snowflake's position: drop downward (decrease z).
        for sf in snowflakes:
            sf['z'] -= speed * dt
            # Optionally, add a slight horizontal drift:
            # sf['x'] += random.uniform(-0.005, 0.005) * dt
            # sf['y'] += random.uniform(-0.005, 0.005) * dt

            # Respawn the snowflake at the top if it falls below the tree.
            if sf['z'] < tree_z_min:
                sf['x'] = random.uniform(tree_x_min, tree_x_max)
                sf['y'] = random.uniform(tree_y_min, tree_y_max)
                sf['z'] = tree_z_max

    # Turn off all LEDs when the animation ends.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Adjust 'coordinates.csv' to your CSV file path if needed.
    animate_snowflake_paths('coordinates.csv', duration=30, interval=0.05,
                             num_snowflakes=50, speed=5, threshold=1.0)
