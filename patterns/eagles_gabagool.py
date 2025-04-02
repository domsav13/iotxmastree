import time
import math
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def animate_spiral_team_colors(csv_file, duration=30, interval=0.05, speed=2.0, spiral_factor=4*math.pi, team='eagles'):
    """
    Animate a spiral pattern on a 3D LED tree using discrete team colors.
    
    For each LED, we compute a phase based on:
      - Its polar angle (theta) relative to the tree center (x,y).
      - Its normalized height (z).
      - A time-dependent offset.
    
    That phase is wrapped into [0, 2π] and mapped to one of the discrete team colors.
    
    Parameters:
      csv_file (str): CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Animation duration in seconds.
      interval (float): Delay between frame updates in seconds.
      speed (float): Angular speed multiplier for the time offset.
      spiral_factor (float): Amount of twist (in radians) over the tree’s height.
      team (str): Either 'eagles' or 'italian' to select the corresponding color palette.
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
    
    # Define team color palettes in GRB order.
    if team.lower() == 'eagles':
        # Philadelphia Eagles palette in GRB:
        # Midnight Green: (76, 0, 84)
        # Silver:         (172, 165, 175)
        # Black:          (0, 0, 0)
        # White:          (255, 255, 255)
        team_colors = [
            (76, 0, 84),
            (172, 165, 175),
            (0, 0, 0),
            (255, 255, 255)
        ]
    elif team.lower() == 'italian':
        # Italian flag palette in GRB:
        # Italian Green: (146, 0, 70)
        # White:         (255, 255, 255)
        # Italian Red:   (43, 206, 55)
        team_colors = [
            (146, 0, 70),
            (255, 255, 255),
            (43, 206, 55)
        ]
    else:
        # Fallback to a simple palette.
        team_colors = [(0,255,0)]
    
    num_colors = len(team_colors)
    
    start_time = time.time()
    while time.time() - start_time < duration:
        t = time.time() - start_time
        for idx, row in df.iterrows():
            x, y, z = row['X'], row['Y'], row['Z']
            # Compute polar angle (theta) relative to tree center.
            theta = math.atan2(y - y_center, x - x_center)
            # Normalize z (height) to [0, 1].
            norm_z = (z - z_min) / (z_max - z_min) if (z_max - z_min) else 0
            # Compute the spiral phase.
            phase = theta + norm_z * spiral_factor + speed * t
            phase = phase % (2 * math.pi)
            # Map the phase to a discrete color index.
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
    # To display the Eagles colors, use team='eagles'
    animate_spiral_team_colors('coordinates.csv', duration=30, interval=0.05, speed=2.0, spiral_factor=4*math.pi, team='eagles')
    # To display the Italian flag, change team='italian'
