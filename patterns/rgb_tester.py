import time
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def light_tree(rgb_color, csv_file='coordinates.csv', duration=30):
    """
    Lights all LEDs on the tree with the given RGB color for the specified duration.
    
    Parameters:
      rgb_color (tuple): Desired color as an (R, G, B) tuple.
      csv_file (str): Path to the CSV file with LED coordinates.
      duration (float): How long (in seconds) to display the color.
    """
    # Load LED coordinates from the CSV.
    df = pd.read_csv(csv_file)
    df['led_index'] = df.index
    LED_COUNT = len(df)
    
    # LED strip configuration.
    LED_PIN        = 18           # GPIO pin (data signal)
    LED_FREQ_HZ    = 800000       # LED signal frequency in hertz
    LED_DMA        = 10           # DMA channel for signal generation
    LED_BRIGHTNESS = 125          # Brightness (0 to 255)
    LED_INVERT     = False        # True to invert the signal if needed
    LED_CHANNEL    = 0            # Set to 0 for GPIO 18
    
    # Initialize the LED strip.
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                       LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    
    # Set every LED to the specified RGB color.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(rgb_color[0], rgb_color[1], rgb_color[2]))
    strip.show()
    
    # Keep the color displayed for the specified duration.
    time.sleep(duration)
    
    # Turn off all the LEDs.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Prompt the user to enter an RGB value.
    user_input = input("Enter an RGB value as R,G,B (e.g., 255,0,0 for red): ")
    try:
        # Split and parse the input string.
        parts = user_input.split(',')
        if len(parts) != 3:
            raise ValueError("You must enter exactly three values separated by commas.")
        r = int(parts[0].strip())
        g = int(parts[1].strip())
        b = int(parts[2].strip())
        rgb_color = (r, g, b)
        print("Setting tree color to:", rgb_color)
        light_tree(rgb_color, csv_file='coordinates.csv', duration=30)
    except Exception as e:
        print("Error parsing RGB value:", e)
