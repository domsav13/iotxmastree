import time
import random
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def heat_to_color(heat):
    """
    Map a heat value (0–255) to an RGB color.
    This common mapping produces a fire-like palette:
      - Low heat: black to red,
      - Mid heat: red to orange,
      - High heat: orange to yellow.
    """
    if heat < 85:
        # Scale from black to red.
        return (heat * 3, 0, 0)
    elif heat < 170:
        # Scale from red to orange.
        return (255, (heat - 85) * 3, 0)
    else:
        # Scale from orange to yellow.
        return (255, 255, (heat - 170) * 3)

def animate_fireplace(csv_file, duration=30, interval=0.05, cooling=55, sparking=120):
    """
    Animate a calm, fireplace-style flame on a 3D LED tree.
    
    The effect simulates a fire at the bottom of the tree by:
      1. Sorting the LEDs by their Z coordinate.
      2. Using a "heat" array (0–255) that is cooled, diffused upward,
         and occasionally ignited at the bottom.
      3. Mapping the heat to a fire color palette.
    
    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Total animation duration in seconds.
      interval (float): Delay between frames (seconds).
      cooling (int): Cooling factor to lower the heat (higher cools faster).
      sparking (int): Likelihood (0–255) of new sparks at the base.
    """
    # Load LED coordinates.
    df = pd.read_csv(csv_file)
    df['led_index'] = df.index
    # Sort by Z coordinate so that lower LEDs (base of tree) come first.
    df_sorted = df.sort_values('Z').reset_index(drop=True)
    LED_COUNT = len(df_sorted)

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

    # Initialize heat for each LED.
    heat = [0] * LED_COUNT

    animation_start = time.time()
    while time.time() - animation_start < duration:
        # 1. Cool down every cell a little.
        for i in range(LED_COUNT):
            cooldown = random.randint(0, ((cooling * 10) // LED_COUNT) + 2)
            heat[i] = max(0, heat[i] - cooldown)

        # 2. Heat diffusion upward.
        # For each LED (from top down), let its heat be influenced by the lower LEDs.
        for i in range(LED_COUNT - 1, 1, -1):
            heat[i] = (heat[i - 1] + heat[i - 2] + heat[i - 2]) // 3

        # 3. Randomly ignite new sparks near the bottom.
        if random.randint(0, 255) < sparking:
            y = random.randint(0, min(7, LED_COUNT - 1))
            heat[y] = min(255, heat[y] + random.randint(160, 255))

        # 4. Map heat to color and update the LED strip.
        for i in range(LED_COUNT):
            color = heat_to_color(heat[i])
            # Retrieve the physical LED index from the sorted DataFrame.
            physical_index = int(df_sorted.iloc[i]['led_index'])
            strip.setPixelColor(physical_index, Color(*color))
        strip.show()
        time.sleep(interval)

    # Turn off all LEDs when finished.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Replace 'coordinates.csv' with your CSV file path if needed.
    animate_fireplace('coordinates.csv', duration=30, interval=0.05, cooling=55, sparking=120)
