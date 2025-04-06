import time
import math
import random
import pandas as pd
from rpi_ws281x import PixelStrip, Color

def animate_random_planes(csv_file, duration=30, interval=0.01, plane_speed=50.0, thickness_factor=0.1):
    """
    Animate random planes passing through the LED tree.
    
    For each plane:
      - A random unit normal vector (A, B, C) is generated.
      - Each LED’s projection onto this vector is computed to find the range (min_p, max_p).
      - A plane of thickness (thickness = thickness_factor * (max_p-min_p)) is animated by
        moving its offset D from (min_p - thickness) to (max_p + thickness) at a rate of plane_speed.
      - LEDs with a distance from the plane less than thickness/2 are lit with a random color.
      - After the plane passes through, a new plane is generated.
    
    Parameters:
      csv_file (str): Path to CSV file with LED coordinates (columns: X, Y, Z).
      duration (float): Total duration of the animation in seconds.
      interval (float): Time (in seconds) between frame updates.
      plane_speed (float): Speed (in coordinate units per second) at which the plane moves.
      thickness_factor (float): Fraction of the projection range used as the plane’s thickness.
    """
    # Load LED coordinates.
    df = pd.read_csv(csv_file)
    df['led_index'] = df.index
    LED_COUNT = len(df)
    
    # LED strip configuration.
    LED_PIN        = 18            # GPIO pin (data signal)
    LED_FREQ_HZ    = 800000        # LED signal frequency in hertz
    LED_DMA        = 10            # DMA channel for signal generation
    LED_BRIGHTNESS = 125           # Brightness (0 to 255)
    LED_INVERT     = False         # True to invert the signal if needed
    LED_CHANNEL    = 0             # Set to 0 for GPIO 18
    strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                       LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
    strip.begin()
    
    overall_start = time.time()
    while time.time() - overall_start < duration:
        # Generate a random plane:
        A = random.uniform(-1, 1)
        B = random.uniform(-1, 1)
        C = random.uniform(-1, 1)
        norm = math.sqrt(A*A + B*B + C*C)
        if norm == 0:
            continue
        A /= norm
        B /= norm
        C /= norm
        
        # For each LED, compute the projection p = A*x + B*y + C*z.
        projections = []
        for _, row in df.iterrows():
            p = A * row['X'] + B * row['Y'] + C * row['Z']
            projections.append(p)
        min_p = min(projections)
        max_p = max(projections)
        proj_range = max_p - min_p
        
        # Set plane thickness as a fraction of the projection range.
        thickness = thickness_factor * proj_range
        
        # Start the plane at D = min_p - thickness and move to D = max_p + thickness.
        D = min_p - thickness
        end_D = max_p + thickness
        
        # Choose a random color for this plane.
        plane_color = Color(random.randint(0,255), random.randint(0,255), random.randint(0,255))
        
        plane_start = time.time()
        prev_time = plane_start
        # Animate the plane as long as it hasn't passed end_D and total duration not exceeded.
        while D < end_D and (time.time() - overall_start) < duration:
            # For each LED, compute its distance from the plane: |A*x+B*y+C*z+D|.
            for _, row in df.iterrows():
                x, y, z = row['X'], row['Y'], row['Z']
                distance = abs(A * x + B * y + C * z + D)
                if distance <= thickness/2:
                    strip.setPixelColor(int(row['led_index']), plane_color)
                else:
                    strip.setPixelColor(int(row['led_index']), Color(0, 0, 0))
            strip.show()
            time.sleep(interval)
            
            # Update D based on elapsed time.
            current_time = time.time()
            dt = current_time - prev_time
            prev_time = current_time
            D += plane_speed * dt
        # End of one plane pass. Loop will choose a new random plane.
    
    # Turn off all LEDs after the animation.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()

if __name__ == '__main__':
    animate_random_planes('coordinates.csv', duration=30, interval=0.01, plane_speed=25, thickness_factor=0.5)
