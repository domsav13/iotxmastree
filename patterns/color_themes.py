import time
import math
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def apply_gamma(color, gamma=2.2):
    """
    Apply gamma correction to an (R, G, B) tuple.
    The input values are assumed to be in the 0–255 range.
    Returns a new (R, G, B) tuple with gamma correction applied.
    """
    r, g, b = color
    r_corr = int(((r / 255.0) ** (1.0 / gamma)) * 255)
    g_corr = int(((g / 255.0) ** (1.0 / gamma)) * 255)
    b_corr = int(((b / 255.0) ** (1.0 / gamma)) * 255)
    return (r_corr, g_corr, b_corr)

def animate_spiral_team_colors(csv_file, duration=30, interval=0.05,
                               speed=2.0, spiral_factor=4*math.pi, team='gwu'):
    """
    Animate a spiral pattern on a 3D LED tree using discrete color palettes.
    
    Each LED’s (x, y, z) coordinate is used to compute a phase:
        phase = theta + (normalized_z * spiral_factor) + (speed * time)
    The phase (wrapped into [0, 2π]) is then used to select one of the discrete team colors.
    
    Colors are defined in GRB order (as expected by your LED strip). Gamma correction
    is applied so that when brightness is reduced (LED_BRIGHTNESS < 255) the perceived colors
    match the intended values.
    
    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Animation duration in seconds.
      interval (float): Delay between frame updates (seconds).
      speed (float): Speed multiplier for the time offset.
      spiral_factor (float): Amount of twist (in radians) over the tree’s height.
      team (str): Color theme key (e.g. 'eagles', 'italian', 'gwu').
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

    # Define the color palettes in GRB order.
    # (Remember: The first tuple value is G, the second is R, the third is B.)
    # Eagles
    eagles_colors = [
        (76, 0, 84),    # Midnight Green
        (106, 4, 56),   # Green
        (96, 96, 98),   # Silver
        (255, 255, 255),# White
        (187, 76, 23)   # Kelly Green
    ]
    # Italian
    italian_colors = [
        (140, 0, 69),   # Green
        (33, 205, 42),  # Red
        (255, 255, 255) # White
    ]
    # GWU (Pantone 302, Pantone 7503, White)
    # Standard RGB for Pantone 302 is (0, 57, 77); for GRB, swap to (57, 0, 77).
    # Standard RGB for Pantone 7503 is (168, 153, 129); for GRB, swap to (153, 168, 129).
    # White is (255, 255, 255) in both.
    gwu_colors = [
        (57, 0, 77),     # Pantone 302
        (153, 168, 129), # Pantone 7503
        (255, 255, 255)  # White
    ]

    # Dictionary of color themes.
    color_themes = {
        'eagles': eagles_colors,
        'italian': italian_colors,
        'gwu': gwu_colors
    }

    # Get the color palette for the chosen theme, default to 'gwu' if invalid.
    team = team.lower()
    team_colors = color_themes.get(team, gwu_colors)

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
            phase %= (2 * math.pi)
            # Map phase into one of the discrete colors in the chosen palette.
            color_index = int((phase / (2 * math.pi)) * num_colors) % num_colors
            base_color = team_colors[color_index]
            # Apply gamma correction.
            corrected_color = apply_gamma(base_color, gamma=2.2)
            # Send to LED strip.
            strip.setPixelColor(int(row['led_index']), Color(*corrected_color))
        strip.show()
        time.sleep(interval)

    # Turn off all LEDs when finished.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Prompt the user for the color theme.
    themes = ['eagles', 'italian', 'gwu']
    print("Available color themes:", ", ".join(themes))
    chosen_theme = input("Which theme would you like to use? ").strip().lower()
    
    if chosen_theme not in themes:
        print(f"Theme '{chosen_theme}' not recognized. Defaulting to 'gwu'.")
        chosen_theme = 'gwu'
    
    # Run the animation.
    animate_spiral_team_colors('coordinates.csv', duration=30, interval=0.05, 
                               speed=2.0, spiral_factor=4*math.pi, team=chosen_theme)
