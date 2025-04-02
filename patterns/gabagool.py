import time
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def lerp_color(c1, c2, t):
    """
    Linearly interpolate between two colors (each a tuple of (R, G, B))
    using the factor t in [0, 1].
    """
    r = int(c1[0] + (c2[0] - c1[0]) * t)
    g = int(c1[1] + (c2[1] - c1[1]) * t)
    b = int(c1[2] + (c2[2] - c1[2]) * t)
    return (r, g, b)

def get_italian_color(t):
    """
    Given a parameter t in [0,1], return a color from a continuous gradient
    that cycles through the Italian flag colors (in GRB order):
      - Green: (146, 0, 70)
      - White: (255, 255, 255)
      - Red:   (43, 206, 55)
    
    The gradient is divided into three segments:
      Segment 1: green to white (t in [0, 1/3])
      Segment 2: white to red   (t in [1/3, 2/3])
      Segment 3: red to green   (t in [2/3, 1])
    """
    # Define the colors (in GRB order)
    green = (146, 0, 70)
    white = (255, 255, 255)
    red   = (43, 206, 55)
    
    if t < 1/3:
        # Interpolate from green to white.
        t2 = t / (1/3)
        return lerp_color(green, white, t2)
    elif t < 2/3:
        # Interpolate from white to red.
        t2 = (t - 1/3) / (1/3)
        return lerp_color(white, red, t2)
    else:
        # Interpolate from red back to green.
        t2 = (t - 2/3) / (1/3)
        return lerp_color(red, green, t2)

def animate_italian_flag(csv_file, duration=30, interval=0.05, speed=0.2):
    """
    Animate a continuous color wave on your LED tree using the Italian flag colors.
    
    Each LED's color is determined by a phase computed from its position (based on its index)
    and a time-dependent offset. The phase is mapped to a gradient that cycles through green,
    white, and red (in GRB order), then the LED strip is updated accordingly.
    
    Parameters:
      csv_file (str): Path to the CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Animation duration in seconds.
      interval (float): Delay (in seconds) between LED updates.
      speed (float): Speed multiplier for the color wave.
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
    
    start_time = time.time()
    while time.time() - start_time < duration:
        t = time.time() - start_time
        # For each LED, compute a phase and determine its color.
        for idx, row in df.iterrows():
            base_phase = idx / LED_COUNT
            # Adding a time component makes the gradient move; speed controls the rate.
            phase = (base_phase + t * speed) % 1.0
            color_tuple = get_italian_color(phase)
            strip.setPixelColor(int(row['led_index']), Color(*color_tuple))
        strip.show()
        time.sleep(interval)
    
    # Turn off all LEDs after the animation.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Replace 'coordinates.csv' with your LED coordinate CSV file if needed.
    animate_italian_flag('coordinates.csv', duration=30, interval=0.05, speed=0.2)
