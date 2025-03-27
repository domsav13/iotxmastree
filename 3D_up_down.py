import time
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def animate_wave(csv_file, interval=0.05, duration=30, wave_thickness_ratio=0.1, 
                 wave_color=Color(255, 0, 0), background_color=Color(255, 255, 255), wave_speed=2.0):
    """
    Animate a green wave (a band of lit LEDs) moving up and down the tree, 
    with all other LEDs initially white.
    
    After the animation completes, all LEDs are turned off.
    
    Parameters:
      csv_file (str): Path to the CSV file with LED coordinates (columns: X, Y, Z)
      interval (float): Time in seconds between LED updates.
      duration (float): Total duration in seconds for the animation.
      wave_thickness_ratio (float): Fraction of the total tree height used as the thickness of the wave.
      wave_color: LED color for the wave (green).
      background_color: LED color for the background (white).
      wave_speed (float): Multiplier for the wave's movement speed.
    """
    # Load LED coordinates; assume physical order corresponds to CSV row order.
    df = pd.read_csv(csv_file)
    df['led_index'] = df.index
    df_sorted = df.sort_values('Z').reset_index(drop=True)
    
    # Determine the tree's vertical span and set the wave's thickness.
    tree_z_min = df_sorted['Z'].min()
    tree_z_max = df_sorted['Z'].max()
    tree_height = tree_z_max - tree_z_min
    wave_thickness = tree_height * wave_thickness_ratio

    # LED strip configuration:
    LED_COUNT      = len(df)       # Total number of LEDs
    LED_PIN        = 18            # GPIO pin (data signal)
    LED_FREQ_HZ    = 800000        # LED signal frequency in hertz
    LED_DMA        = 10            # DMA channel to use for generating signal
    LED_BRIGHTNESS = 125           # Brightness (0 to 255)
    LED_INVERT     = False         # True to invert the signal (if needed)
    LED_CHANNEL    = 0             # Set to 0 for GPIO 18

    # Initialize the LED strip.
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    # Calculate movement parameters.
    total_steps = duration / interval
    half_steps = total_steps / 2
    delta = tree_height / half_steps  # Base delta per update

    wave_position = tree_z_min
    direction = 1  # 1 for upward, -1 for downward

    start_time = time.time()
    while time.time() - start_time < duration:
        # For each LED, if its Z coordinate falls within the wave band, light it green; otherwise, set it white.
        for _, row in df_sorted.iterrows():
            led_z = row['Z']
            physical_index = int(row['led_index'])  # Ensure index is a native Python int
            if abs(led_z - wave_position) <= wave_thickness / 2:
                strip.setPixelColor(physical_index, wave_color)
            else:
                strip.setPixelColor(physical_index, background_color)
        strip.show()
        time.sleep(interval)
        
        # Update the wave position, multiplying delta by wave_speed to move faster.
        wave_position += direction * delta * wave_speed
        if wave_position > tree_z_max:
            wave_position = tree_z_max
            direction = -1
        elif wave_position < tree_z_min:
            wave_position = tree_z_min
            direction = 1

    # Once the animation is complete, turn off all the LEDs.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    animate_wave('coordinates.csv', interval=0.01, duration=30, 
                 wave_thickness_ratio=0.2, wave_color=Color(255, 0, 0), 
                 background_color=Color(255, 255, 255), wave_speed=10.0)
