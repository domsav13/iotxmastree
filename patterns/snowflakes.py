import time
import random
import math
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def animate_snowflakes(csv_file, duration=30, interval=0.05, num_snowflakes=5, speed=0.1, threshold=0.2):
    """
    Animate a snowflake effect on a 3D LED tree.
    
    Snowflake particles (shown in white) are simulated starting at the top of the tree.
    They fall downward (with a slight horizontal drift) and "light up" any LED whose position
    is within a certain distance (threshold) of the snowflake. When a snowflake falls below the tree,
    it is respawned at the top.
    
    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Total duration of the animation in seconds.
      interval (float): Delay (in seconds) between animation frames.
      num_snowflakes (int): Number of snowflake particles to simulate.
      speed (float): Falling speed of the snowflakes (in coordinate units per second).
      threshold (float): Maximum distance for a snowflake to affect an LED.
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

    # Determine tree bounds.
    tree_x_min, tree_x_max = df['X'].min(), df['X'].max()
    tree_y_min, tree_y_max = df['Y'].min(), df['Y'].max()
    tree_z_min, tree_z_max = df['Z'].min(), df['Z'].max()

    # Initialize snowflake particles.
    # Each snowflake is represented as a dict with its current (x, y, z) position and velocities.
    snowflakes = []
    for _ in range(num_snowflakes):
        snowflake = {
            'x': random.uniform(tree_x_min, tree_x_max),
            'y': random.uniform(tree_y_min, tree_y_max),
            'z': tree_z_max,  # Start at the top of the tree.
            'vx': random.uniform(-0.02, 0.02),  # Small horizontal drift.
            'vy': random.uniform(-0.02, 0.02),
            'vz': -speed  # Falling downward.
        }
        snowflakes.append(snowflake)

    animation_start = time.time()
    prev_time = animation_start

    while time.time() - animation_start < duration:
        current_time = time.time()
        dt = current_time - prev_time
        prev_time = current_time

        # Clear all LEDs.
        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(0, 0, 0))

        # Update snowflake positions.
        for sf in snowflakes:
            sf['x'] += sf['vx'] * dt
            sf['y'] += sf['vy'] * dt
            sf['z'] += sf['vz'] * dt

            # If a snowflake has fallen below the tree, respawn it at the top.
            if sf['z'] < tree_z_min:
                sf['x'] = random.uniform(tree_x_min, tree_x_max)
                sf['y'] = random.uniform(tree_y_min, tree_y_max)
                sf['z'] = tree_z_max
                sf['vx'] = random.uniform(-0.02, 0.02)
                sf['vy'] = random.uniform(-0.02, 0.02)
                sf['vz'] = -speed

        # For each LED, check if any snowflake is within the threshold distance.
        for idx, row in df.iterrows():
            led_x, led_y, led_z = row['X'], row['Y'], row['Z']
            for sf in snowflakes:
                dx = led_x - sf['x']
                dy = led_y - sf['y']
                dz = led_z - sf['z']
                distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                if distance <= threshold:
                    # Light up the LED in white.
                    strip.setPixelColor(int(row['led_index']), Color(255, 255, 255))
                    break  # Only need one snowflake to light up this LED.
        strip.show()
        time.sleep(interval)

    # Turn off all LEDs when finished.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Change 'coordinates.csv' to the path of your CSV file if necessary.
    animate_snowflakes('coordinates.csv', duration=30, interval=0.05,
                         num_snowflakes=5, speed=0.1, threshold=0.2)
