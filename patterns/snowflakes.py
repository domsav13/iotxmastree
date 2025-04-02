import time
import random
import math
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def animate_snowflakes(csv_file, duration=30, interval=0.05, num_snowflakes=5, speed=0.1, threshold=1.0, debug=False):
    """
    Animate a snowflake effect on a 3D LED tree.
    
    Snowflake particles (displayed in white) are simulated starting at the top of the tree.
    They fall downward (with a slight horizontal drift) and "light up" any LED whose position
    is within a specified threshold distance of the snowflake. When a snowflake falls below the tree,
    it is respawned at the top.
    
    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Total duration of the animation in seconds.
      interval (float): Delay between animation frames (in seconds).
      num_snowflakes (int): Number of snowflake particles to simulate.
      speed (float): Falling speed of the snowflakes (in coordinate units per second).
      threshold (float): Maximum distance for a snowflake to affect an LED.
      debug (bool): If True, print debugging information.
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

    # Initialize snowflake particles.
    # Each snowflake is a dictionary with its current (x, y, z) position and velocities.
    snowflakes = []
    for _ in range(num_snowflakes):
        snowflake = {
            'x': random.uniform(tree_x_min, tree_x_max),
            'y': random.uniform(tree_y_min, tree_y_max),
            'z': tree_z_max,  # Start at the top.
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

            # Respawn the snowflake at the top if it falls below the tree.
            if sf['z'] < tree_z_min:
                sf['x'] = random.uniform(tree_x_min, tree_x_max)
                sf['y'] = random.uniform(tree_y_min, tree_y_max)
                sf['z'] = tree_z_max
                sf['vx'] = random.uniform(-0.02, 0.02)
                sf['vy'] = random.uniform(-0.02, 0.02)
                sf['vz'] = -speed

        # Check each LED to see if it's close enough to any snowflake.
        for idx, row in df.iterrows():
            led_x, led_y, led_z = row['X'], row['Y'], row['Z']
            led_lit = False
            for sf in snowflakes:
                dx = led_x - sf['x']
                dy = led_y - sf['y']
                dz = led_z - sf['z']
                distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                if debug and idx == 0:
                    print(f"LED0 distance to snowflake: {distance:.2f}")
                if distance <= threshold:
                    # Light this LED white.
                    strip.setPixelColor(int(row['led_index']), Color(255, 255, 255))
                    led_lit = True
                    break  # Only one snowflake needed to light the LED.
            if not led_lit:
                # Optional: ensure the LED is off if not lit.
                strip.setPixelColor(int(row['led_index']), Color(0, 0, 0))
        strip.show()
        time.sleep(interval)

    # Turn off all LEDs after the animation.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Adjust 'coordinates.csv' to your file path if needed.
    # For troubleshooting, you can set debug=True and adjust threshold to a higher value.
    animate_snowflakes('coordinates.csv', duration=30, interval=0.05,
                         num_snowflakes=5, speed=0.1, threshold=1.0, debug=True)
