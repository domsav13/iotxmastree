import time
import random
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def heat_to_color(heat):
    """
    Map a heat value (0–255) to an RGB color in GRB order for a fire-like palette:
      - Low heat (0–84): black to red,
      - Mid heat (85–169): red to orange,
      - High heat (170–255): orange to yellow.
    """
    if heat < 85:
        # Black to red: in GRB, red is in the second position.
        return (0, heat * 3, 0)
    elif heat < 170:
        # Red to orange: increasing green component.
        return ((heat - 85) * 3, 255, 0)
    else:
        # Orange to yellow: increase blue component.
        return (255, 255, (heat - 170) * 3)

def animate_fireplace(csv_file, duration=30, interval=0.05, cooling=55, sparking=120):
    """
    Animate a fireplace-style flame on a 3D LED tree that reflects a more realistic fire.
    
    In this version:
      - The LEDs are sorted by their Z coordinate (with the base at the bottom).
      - A heat array is cooled, diffused upward, and occasionally ignited at the base.
      - New sparks at the base use modest heat additions so that the base remains mostly red,
        while upward diffusion lets the heat increase into the orange and yellow ranges.
    
    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Total animation duration (seconds).
      interval (float): Delay between frames (seconds).
      cooling (int): Cooling factor (higher values cool faster).
      sparking (int): Likelihood (0–255) of new sparks at the base.
    """
    # Load LED coordinates.
    df = pd.read_csv(csv_file)
    df['led_index'] = df.index
    # Sort LEDs by Z so that the base (lowest Z) is first.
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
        # 1. Cool down every LED a bit.
        for i in range(LED_COUNT):
            cooldown = random.randint(0, ((cooling * 10) // LED_COUNT) + 2)
            heat[i] = max(0, heat[i] - cooldown)

        # 2. Diffuse the heat upward.
        # Each LED (from the top down) gets some influence from the ones below.
        for i in range(LED_COUNT - 1, 1, -1):
            heat[i] = (heat[i - 1] + heat[i - 2] + heat[i - 2]) // 3

        # 3. Randomly ignite new sparks near the base.
        # Instead of adding very high heat (which would yield orange/yellow), we add modest values.
        if random.randint(0, 255) < sparking:
            y = random.randint(0, min(7, LED_COUNT - 1))  # Only in the bottom region.
            heat[y] = min(255, heat[y] + random.randint(20, 80))  # Lower spark values.

        # 4. Map heat to color and update the LED strip.
        for i in range(LED_COUNT):
            color = heat_to_color(heat[i])
            # Use the physical LED index from the sorted DataFrame.
            physical_index = int(df_sorted.iloc[i]['led_index'])
            strip.setPixelColor(physical_index, Color(*color))
        strip.show()
        time.sleep(interval)

    # Turn off all LEDs after the animation.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Replace 'coordinates.csv' with your CSV file path if needed.
    animate_fireplace('coordinates.csv', duration=30, interval=0.05, cooling=55, sparking=120)
