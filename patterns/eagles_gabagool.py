import time
import math
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def animate_spiral_team_colors_RGB(csv_file, duration=30, interval=0.05, speed=2.0, spiral_factor=4*math.pi, team='eagles'):
    """
    Animate a spiral pattern on a 3D LED tree using discrete team colors.
    
    Each LED’s (x, y, z) coordinate is used to compute a phase:
        phase = theta + (normalized_z * spiral_factor) + (speed * time)
    The phase (wrapped into [0, 2π]) is then used to select one of the discrete team colors.
    
    Colors are defined in GRB order (as expected by your LED strip).
    
    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Animation duration in seconds.
      interval (float): Delay between frame updates (seconds).
      speed (float): Speed multiplier for the time offset.
      spiral_factor (float): Amount of twist (in radians) over the tree’s height.
      team (str): Either 'eagles' or 'italian' to select the color palette.
    """
    # Load LED coordinates.
    df = pd.read_csv(csv_file)
    df['led_index'] = df.index
    LED_COUNT = len(df)
    
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
    
    # Compute the (x, y) center of the tree.
    x_center = (df['X'].min() + df['X'].max()) / 2.0
    y_center = (df['Y'].min() + df['Y'].max()) / 2.0
    # Determine the z range for normalization.
    z_min = df['Z'].min()
    z_max = df['Z'].max()
    
    # Define team palettes in GRB order.
    if team.lower() == 'eagles':
        team_colors = [
            (76, 0, 84),      # Midnight Green GRB
            (106, 4, 56),     # Green GRB
            (96, 96, 98),     # Silver GRB
            (255, 255, 255),  # White
            (187, 76, 23)     # Kelly Green GRB
        ]
    elif team.lower() == 'italian':
        team_colors = [
            (255, 0, 0),     # Italian Green GRB
            (0, 255, 0),    # Italian Red GRB
            (255, 255, 255)   # White
        ]
    else:
        team_colors = [(0, 255, 0)]
    
    num_colors = len(team_colors)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        t = time.time() - start_time
        for idx, row in df.iterrows():
            x, y, z = row['X'], row['Y'], row['Z']
            # Compute polar angle (theta) relative to the tree center.
            theta = math.atan2(y - y_center, x - x_center)
            # Normalize z (height) to [0, 1].
            norm_z = (z - z_min) / (z_max - z_min) if (z_max - z_min) else 0
            # Compute the spiral phase.
            phase = theta + norm_z * spiral_factor + speed * t
            phase %= (2 * math.pi)
            # Map phase into one of the discrete team colors.
            color_index = int((phase / (2 * math.pi)) * num_colors) % num_colors
            color = team_colors[color_index]
            strip.setPixelColor(int(row['led_index']), Color(*color))
        strip.show()
        time.sleep(interval)
    
    # Turn off all LEDs when finished.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # To test the Eagles palette, use team='eagles'.
    # To test the Italian flag, change team='italian'.
    animate_spiral_team_colors_RGB('coordinates.csv', duration=30, interval=0.05, speed=2.0, spiral_factor=4*math.pi, team='italian')
