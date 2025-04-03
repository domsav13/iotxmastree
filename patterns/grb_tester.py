import time
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def apply_gamma(color, gamma=2.2):
    """
    Apply gamma correction to a (R, G, B) tuple.
    The input values are assumed to be in the 0–255 range.
    Returns a new (R, G, B) tuple with gamma correction applied.
    """
    r, g, b = color
    r_corr = int(((r / 255.0) ** (1.0 / gamma)) * 255)
    g_corr = int(((g / 255.0) ** (1.0 / gamma)) * 255)
    b_corr = int(((b / 255.0) ** (1.0 / gamma)) * 255)
    return (r_corr, g_corr, b_corr)

def light_tree(grb_color, csv_file='coordinates.csv', duration=30, gamma=2.2):
    """
    Lights all LEDs on the tree with the given GRB color for the specified duration.
    
    Parameters:
      grb_color (tuple): Desired color as a (G, R, B) tuple.
      csv_file (str): Path to the CSV file with LED coordinates.
      duration (float): How long (in seconds) to display the color.
      gamma (float): Gamma correction value.
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
    
    # Apply gamma correction to the input GRB color.
    # Note: The input is in GRB order, but apply_gamma expects (R, G, B).
    # So we swap the first two values before gamma correction, then swap back.
    # That is, convert input (G, R, B) to (R, G, B):
    rgb_color = (grb_color[1], grb_color[0], grb_color[2])
    corrected_rgb = apply_gamma(rgb_color, gamma=gamma)
    # Swap back to GRB order for the LED strip:
    corrected_grb = (corrected_rgb[1], corrected_rgb[0], corrected_rgb[2])
    
    # Set every LED to the gamma-corrected GRB color.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(corrected_grb[0], corrected_grb[1], corrected_grb[2]))
    strip.show()
    
    # Keep the color displayed for the specified duration.
    time.sleep(duration)
    
    # Turn off all the LEDs.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Prompt the user to enter a GRB value.
    user_input = input("Enter a GRB value as G,R,B (e.g., 255,0,0 for green): ")
    try:
        parts = user_input.split(',')
        if len(parts) != 3:
            raise ValueError("You must enter exactly three values separated by commas.")
        g = int(parts[0].strip())
        r = int(parts[1].strip())
        b = int(parts[2].strip())
        grb_color = (g, r, b)
        # Optionally, you can also prompt for a gamma value:
        gamma_input = input("Enter gamma value (default is 2.2): ")
        if gamma_input.strip() == "":
            gamma_val = 2.2
        else:
            gamma_val = float(gamma_input.strip())
        print("Setting tree color (GRB) to:", grb_color, "with gamma =", gamma_val)
        light_tree(grb_color, csv_file='coordinates.csv', duration=30, gamma=gamma_val)
    except Exception as e:
        print("Error parsing input:", e)
