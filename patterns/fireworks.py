import time
import random
import math
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def animate_fireworks(csv_file, duration=30, interval=0.05,
                      firework_duration=0.75, spawn_chance=0.05, blast_radius_factor=0.5):
    """
    Animate random firework effects on a 3D LED tree with overlapping bursts using color groups.

    Each firework burst is centered on a random LED. Its blast covers all LEDs within a
    radius defined by blast_radius_factor * (tree's maximum dimension). A color group is chosen
    (e.g., red/orange/yellow, pink/purple/blue, blue/yellow/white) and each LED in the blast is
    randomly assigned one of those colors. The burst fades out over firework_duration seconds.
    
    Multiple fireworks may be active concurrently (spawned each frame with probability spawn_chance)
    and their color contributions are added together (with values clamped to 255).

    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Total duration (in seconds) for the entire animation.
      interval (float): Time (in seconds) between animation frames.
      firework_duration (float): Duration (in seconds) for each firework burst.
      spawn_chance (float): Probability (per frame) to spawn a new firework.
      blast_radius_factor (float): Factor to set the firework blast radius relative to tree size.
                                   (e.g., 0.5 means the blast radius is 50% of the tree's max dimension)
    """
    # Load LED coordinates; assume CSV rows correspond to physical LED order.
    df = pd.read_csv(csv_file)
    df['led_index'] = df.index

    # LED strip configuration.
    LED_COUNT      = len(df)
    LED_PIN        = 18           # GPIO pin (data signal)
    LED_FREQ_HZ    = 800000       # LED signal frequency in hertz
    LED_DMA        = 10           # DMA channel to use for generating signal
    LED_BRIGHTNESS = 125          # Brightness (0 to 255)
    LED_INVERT     = False        # True to invert the signal (if needed)
    LED_CHANNEL    = 0            # Set to 0 for GPIO 18

    # Initialize the LED strip.
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                       LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()

    # Get tree bounds.
    tree_x_min, tree_x_max = df['X'].min(), df['X'].max()
    tree_y_min, tree_y_max = df['Y'].min(), df['Y'].max()
    tree_z_min, tree_z_max = df['Z'].min(), df['Z'].max()
    max_dim = max(tree_x_max - tree_x_min,
                  tree_y_max - tree_y_min,
                  tree_z_max - tree_z_min)
    # Set the blast radius based on the tree size.
    local_radius = blast_radius_factor * max_dim

    # Define color groups.
    # Note: The rpi_ws281x Color() function uses GRB ordering.
    # To display red (RGB 255, 0, 0) use Color(0, 255, 0), etc.
    group1 = [ (0, 255, 0),    # red
               (69, 255, 0),   # orange (displays as orange)
               (255, 255, 0) ] # yellow

    group2 = [ (105, 255, 180),  # pink (hot pink)
               (0, 128, 128),    # purple
               (0, 0, 255) ]     # blue

    group3 = [ (0, 0, 255),      # blue
               (255, 255, 0),    # yellow
               (255, 255, 255) ] # white

    color_groups = [group1, group2, group3]

    # List to hold active fireworks.
    active_fireworks = []
    # Each firework is a dict with:
    #   'local_leds': list of LED indices affected,
    #   'colors': dict mapping LED index -> base color tuple (r, g, b),
    #   'start_time': creation time,
    #   'duration': firework_duration

    animation_start = time.time()
    while time.time() - animation_start < duration:
        current_time = time.time()

        # Spawn a new firework with probability spawn_chance per frame.
        if random.random() < spawn_chance:
            # Choose a random LED as the burst center.
            center_row = df.sample(n=1).iloc[0]
            center_x, center_y, center_z = center_row['X'], center_row['Y'], center_row['Z']
            # Find all LEDs within local_radius of the center.
            local_leds = []
            for _, row in df.iterrows():
                dx = row['X'] - center_x
                dy = row['Y'] - center_y
                dz = row['Z'] - center_z
                distance = math.sqrt(dx*dx + dy*dy + dz*dz)
                if distance <= local_radius:
                    local_leds.append(int(row['led_index']))
            if not local_leds:
                local_leds = [int(center_row['led_index'])]
            # Choose a random color group.
            chosen_group = random.choice(color_groups)
            # Assign each LED in the blast a random color from the group.
            colors = {}
            for idx in local_leds:
                colors[idx] = random.choice(chosen_group)
            # Create the firework burst.
            firework = {
                'local_leds': local_leds,
                'colors': colors,
                'start_time': current_time,
                'duration': firework_duration
            }
            active_fireworks.append(firework)

        # Create an array for LED color contributions; start with all LEDs off.
        led_contributions = [(0, 0, 0) for _ in range(LED_COUNT)]

        # Process each active firework.
        for fw in active_fireworks:
            age = current_time - fw['start_time']
            if age > fw['duration']:
                continue  # Will be removed below.
            fade = 1.0 - (age / fw['duration'])
            for idx in fw['local_leds']:
                base_r, base_g, base_b = fw['colors'][idx]
                contrib = (int(base_r * fade), int(base_g * fade), int(base_b * fade))
                r_sum, g_sum, b_sum = led_contributions[idx]
                led_contributions[idx] = (r_sum + contrib[0], g_sum + contrib[1], b_sum + contrib[2])

        # Remove expired fireworks.
        active_fireworks = [fw for fw in active_fireworks if current_time - fw['start_time'] < fw['duration']]

        # Update each LED with the combined contributions.
        for i in range(LED_COUNT):
            r, g, b = led_contributions[i]
            # Clamp each channel to a maximum of 255.
            r = min(r, 255)
            g = min(g, 255)
            b = min(b, 255)
            strip.setPixelColor(i, Color(r, g, b))
        strip.show()
        time.sleep(interval)

    # Turn off all LEDs when the animation ends.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    # Change 'coordinates.csv' to the path of your CSV file if needed.
    animate_fireworks('coordinates.csv', duration=30, interval=0.05,
                      firework_duration=0.75, spawn_chance=0.05, blast_radius_factor=1)
