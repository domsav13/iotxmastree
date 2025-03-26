import pandas as pd
import matplotlib.pyplot as plt
import time
import numpy as np

def animate_leds(csv_file, interval=0.2, duration=30):
    """
    Animate the LED lighting effect on a 3D Christmas tree.
    
    Parameters:
        csv_file (str): Path to the CSV file with LED coordinates.
        interval (float): Time in seconds between LED updates.
        duration (float): Total duration in seconds for the animation.
    """
    # Load CSV data with LED coordinates
    df = pd.read_csv(csv_file)
    
    # Sort by 'Z' (vertical axis) so that lower LEDs come first
    df_sorted = df.sort_values('Z').reset_index(drop=True)
    
    # Extract coordinates
    X = df_sorted['X'].values
    Y = df_sorted['Y'].values
    Z = df_sorted['Z'].values
    
    # Set up a 3D scatter plot
    fig = plt.figure()
    ax = fig.add_subplot(111, projection='3d')
    scatter = ax.scatter(X, Y, Z, c='gray', s=50)
    
    # Label axes
    ax.set_xlabel('X')
    ax.set_ylabel('Y')
    ax.set_zlabel('Z')
    
    # Create a sequence that goes from bottom to top then reverses (up and down)
    num_leds = len(df_sorted)
    sequence = list(range(num_leds)) + list(range(num_leds - 2, -1, -1))
    
    start_time = time.time()
    seq_idx = 0
    
    # Loop for the specified duration
    while time.time() - start_time < duration:
        current_led = sequence[seq_idx % len(sequence)]
        
        # Update colors: set all LEDs to gray and the current one to red
        colors = ['gray'] * num_leds
        colors[current_led] = 'red'
        
        # For 3D scatter plots, update both _facecolor3d and _edgecolor3d
        scatter._facecolor3d = scatter._edgecolor3d = plt.cm.colors.to_rgba_array(colors)
        
        # Redraw the figure
        plt.draw()
        plt.pause(interval)
        
        seq_idx += 1

    plt.show()

# Example usage:
if __name__ == '__main__':
    # Path to your CSV file containing the LED coordinates
    animate_leds('coordinates.csv', interval=0.2, duration=30)
