import time
import random
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def heat_to_color(heat):
    """
    Map a heat value (0–255) to an RGB color in GRB order.
    Lower heat values yield red; as heat increases, the color shifts to orange then yellow.
    """
    if heat < 85:
        # Black to red (in GRB: red in second position).
        return (0, heat * 3, 0)
    elif heat < 170:
        # Red to orange.
        return ((heat - 85) * 3, 255, 0)
    else:
        # Orange to yellow.
        return (255, 255, (heat - 170) * 3)

def animate_fireplace(csv_file, duration=30, interval=0.05, cooling=40, sparking=120):
    """
    Animate a realistic fireplace flame on a 3D LED tree.
    
    Adjustments:
      - Sparks now occur within the bottom 30% of the LED strip (by Z coordinate),
        so more LEDs are given an initial heat boost.
      - A reduced cooling factor allows heat to persist and diffuse further upward.
      - As a result, the base remains predominantly red, while the upper regions
        show the transition to orange and yellow/white.
    
    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Animation duration in seconds.
      interval (float): Delay between frames (seconds).
      cooling (int): Cooling factor (lower values let heat persist longer).
      sparking (int): Likelihood (0–255) of new sparks in the spark zone.
    """
    # Load LED coordinates.
    df = pd.read_csv(csv_file)
    df['led_index'] = df.index
    # Sort LEDs by Z so that the base (lowest Z) is first.
    df_sorted = df.sort_values('Z').reset_index(drop=True)
    LED_COUNT = len(df_sorted)

    # LED strip configuration.
    LED_PIN        = 18           
    LED_FREQ_HZ    = 800000       
    LED_DMA        = 10           
    LED_BRIGHTNESS = 125          
    LED_INVERT     = False        
    LED_CHANNEL    = 0            

    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                       LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    # Initialize heat for each LED.
    heat = [0] * LED_COUNT

    animation_start = time.time()
    while time.time() - animation_start < duration:
        # 1. Cool down each LED a bit.
        for i in range(LED_COUNT):
            cooldown = random.randint(0, ((cooling * 10) // LED_COUNT) + 2)
            heat[i] = max(0, heat[i] - cooldown)

        # 2. Diffuse heat upward.
        for i in range(LED_COUNT - 1, 1, -1):
            heat[i] = (heat[i - 1] + heat[i - 2] + heat[i - 2]) // 3

        # 3. Ignite new sparks in the bottom 30% of the LED strip.
        spark_zone = int(LED_COUNT * 0.3)
        if random.randint(0, 255) < sparking:
            y = random.randint(0, max(0, spark_zone - 1))
            # Use modest heat addition so that the base stays mostly red.
            heat[y] = min(255, heat[y] + random.randint(20, 80))

        # 4. Map heat to color and update the LED strip.
        for i in range(LED_COUNT):
            color = heat_to_color(heat[i])
            physical_index = int(df_sorted.iloc[i]['led_index'])
            strip.setPixelColor(physical_index, Color(*color))
        strip.show()
        time.sleep(interval)

    # Turn off all LEDs when the animation ends.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Replace 'coordinates.csv' with your CSV file path if needed.
    animate_fireplace('coordinates.csv', duration=30, interval=0.05, cooling=40, sparking=120)
