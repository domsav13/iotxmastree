import time
import random
import math
import ambient_brightness
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def animate_contagious_effect(csv_file, overall_duration=30, interval=0.01, contagion_speed=1.0, hold_time=0.5):
    """
    Animate a contagious effect on a 3D LED tree.
    One LED is chosen at random as the starting point and its color (randomly generated)
    spreads outwards based on the 3D distance to all other LEDs. Once the entire tree is lit,
    it holds for a moment and then resets before starting the next cycle.
    
    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      overall_duration (float): Total duration (in seconds) for the overall animation.
      interval (float): Time (in seconds) between animation frames.
      contagion_speed (float): Speed at which the contagion spreads (distance units per second).
      hold_time (float): Time (in seconds) to hold the fully lit tree before resetting.
    """
    # Load LED coordinates; assume CSV rows correspond to physical LED order.
    df = pd.read_csv(csv_file)
    df['led_index'] = df.index

    # LED strip configuration:
    LED_COUNT   = len(df)
    LED_PIN     = 18           # GPIO pin (data signal)
    LED_FREQ_HZ = 800000       # LED signal frequency in hertz
    LED_DMA     = 10           # DMA channel to use for generating signal
    LED_BRIGHTNESS = 125       # Brightness (0 to 255)
    LED_INVERT  = False        # True to invert the signal (if needed)
    LED_CHANNEL = 0            # Set to 0 for GPIO 18

    # Initialize the LED strip.
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                       LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    # Create a list of coordinates for convenience.
    led_coords = []
    for _, row in df.iterrows():
        led_coords.append((row['X'], row['Y'], row['Z']))

    animation_start = time.time()
    while time.time() - animation_start < overall_duration:
        # Choose a random LED as the starting point.
        start_idx = random.choice(range(LED_COUNT))
        start_coord = led_coords[start_idx]

        # Generate a random color.
        # Note: rpi_ws281x uses GRB ordering, so if the colors seem off, swap channels accordingly.
        r = random.randint(0, 255)
        g = random.randint(0, 255)
        b = random.randint(0, 255)
        contagion_color = Color(r, g, b)

        # Compute the Euclidean distance from the starting LED to every other LED.
        distances = []
        max_distance = 0
        for coord in led_coords:
            dx = coord[0] - start_coord[0]
            dy = coord[1] - start_coord[1]
            dz = coord[2] - start_coord[2]
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            distances.append(dist)
            if dist > max_distance:
                max_distance = dist

        # Determine how long it takes for the contagion to spread over the full tree.
        spread_duration = max_distance / contagion_speed

        contagion_start = time.time()
        while time.time() - contagion_start < spread_duration:
            elapsed = time.time() - contagion_start
            current_radius = contagion_speed * elapsed

            # For each LED, if its distance from the starting LED is within the current radius,
            # light it up with contagion_color; otherwise, ensure it's turned off.
            for idx in range(LED_COUNT):
                if distances[idx] <= current_radius:
                    strip.setPixelColor(idx, contagion_color)
                else:
                    strip.setPixelColor(idx, Color(0, 0, 0))
            strip.show()
            time.sleep(interval)

        # Once the contagion has reached all LEDs, hold the fully lit tree for a moment.
        for idx in range(LED_COUNT):
            strip.setPixelColor(idx, contagion_color)
        strip.show()
        time.sleep(hold_time)

        # Reset the tree by turning off all LEDs.
        for idx in range(LED_COUNT):
            strip.setPixelColor(idx, Color(0, 0, 0))
        strip.show()
        time.sleep(0.5)  # Short pause before starting the next cycle.

    # Turn off all LEDs when the animation ends.
    for idx in range(LED_COUNT):
        strip.setPixelColor(idx, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Adjust 'coordinates.csv' to match your file location if necessary.
    animate_contagious_effect('coordinates.csv', overall_duration=30, interval=0.01,
                                contagion_speed=8.5, hold_time=0.5)
