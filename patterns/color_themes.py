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
    The phase (wrapped into [0, 2π]) is then used to select one of the discrete palette colors.
    
    Colors are defined in GRB order (as expected by your LED strip). Gamma correction
    is applied so that when brightness is reduced (LED_BRIGHTNESS < 255) the perceived colors
    match the intended values.
    
    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Animation duration in seconds.
      interval (float): Delay between frame updates (seconds).
      speed (float): Speed multiplier for the time offset.
      spiral_factor (float): Amount of twist (in radians) over the tree’s height.
      team (str): Color theme key (e.g. 'eagles', 'italian', 'gwu', 'christmas',
                  'rustic', 'spartans', 'cherry', 'aussie', 'northern', 'sixers').
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
    
    # Define color palettes in GRB order.
    eagles_colors = [
        (76, 0, 84),     # Midnight Green
        (106, 4, 56),    # Green
        (96, 96, 98),    # Silver
        (255, 255, 255), # White
        (187, 76, 23)    # Kelly Green
    ]
    italian_colors = [
        (140, 0, 69),    # Green
        (33, 205, 42),   # Red
        (255, 255, 255)  # White
    ]
    gwu_colors = [
        (57, 0, 77),     # Pantone 302
        (153, 168, 129), # Pantone 7503
        (255, 255, 255)  # White
    ]
    christmas_colors = [
        (50, 1, 32),     # Evergreen
        (34, 178, 34),   # Holly Red
        (255, 255, 255), # Snow White
        (215, 255, 0)    # Gold
    ]
    rustic_colors = [
        (77, 38, 54),    # Deep Pine
        (31, 145, 39),   # Cranberry
        (210, 234, 172), # Warm Beige
        (115, 184, 51)   # Copper
    ]
    spartans_colors = [
        (255, 255, 255), # White
        (144, 30, 255),  # rgb(30,144,255) => GRB
        (215, 255, 0)    # rgb(255,215,0) => GRB
    ]
    cherry_colors = [
        (255, 255, 255), # White
        (182, 255, 193), # Light Pink
        (105, 255, 180)  # Deep Pink
    ]
    aussie_colors = [
        (0, 128, 128),   # Purple (RGB(128,0,128) => GRB(0,128,128))
        (0, 75, 130),    # Dark Purple (RGB(75,0,130) => GRB(0,75,130))
        (51, 102, 153),  # Medium Purple (RGB(102,51,153) => GRB(51,102,153))
        (165, 255, 0),   # Orange (RGB(255,165,0) => GRB(165,255,0))
        (255, 255, 0),   # Yellow
        (0, 0, 255)      # Blue
    ]
    northern_colors = [
        (255, 0, 120),   # Aurora Green
        (50, 0, 255),    # Arctic Blue
        (128, 0, 255),   # Electric Purple
        (180, 0, 80),    # Soft Teal
        (0, 0, 180),     # Midnight Sky
        (100, 0, 200),   # Fading Violet
        (80, 0, 200)     # Plasma Pink
    ]
    # Sixers
    #  Blue:   #006bb6 => RGB(0,107,182) => GRB(107,0,182)
    #  Red:    #ed174c => RGB(237,23,76) => GRB(23,237,76)
    #  Navy:   #002b5c => RGB(0,43,92)   => GRB(43,0,92)
    #  Silver: #c4ced4 => RGB(196,206,212) => GRB(206,196,212)
    sixers_colors = [
        (107, 0, 182),   # Blue
        (23, 237, 76),   # Red
        (43, 0, 92),     # Navy
        (206, 196, 212)  # Silver
    ]
    
    # Dictionary of color themes.
    color_themes = {
        'eagles': eagles_colors,
        'italian': italian_colors,
        'gwu': gwu_colors,
        'christmas': christmas_colors,
        'rustic': rustic_colors,
        'spartans': spartans_colors,
        'cherry': cherry_colors,
        'aussie': aussie_colors,
        'northern': northern_colors,
        'sixers': sixers_colors
    }
    
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
            corrected_color = apply_gamma(base_color, gamma=2.2)
            strip.setPixelColor(int(row['led_index']), Color(*corrected_color))
        strip.show()
        time.sleep(interval)
    
    # Turn off all LEDs when the animation ends.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    themes = [
        'eagles', 'italian', 'gwu', 'christmas', 'rustic',
        'spartans', 'cherry', 'aussie', 'northern', 'sixers'
    ]
    print("Available color themes:", ", ".join(themes))
    chosen_theme = input("Which theme would you like to use? ").strip().lower()
    if chosen_theme not in themes:
        print(f"Theme '{chosen_theme}' not recognized. Defaulting to 'gwu'.")
        chosen_theme = 'gwu'
    animate_spiral_team_colors('coordinates.csv', duration=30, interval=0.05,
                               speed=2.0, spiral_factor=4*math.pi, team=chosen_theme)
