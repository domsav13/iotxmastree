import time
import colorsys
import smbus
import pandas as pd
from rpi_ws281x import PixelStrip, Color

# ====================================================
# BH1750 Sensor Setup (Ambient Light)
# ====================================================
#      - SDA (Data)  → GPIO2 (physical pin 3)
#      - SCL (Clock) → GPIO3 (physical pin 5)
#      - VCC         → 3.3V (or 5V, depending on your sensor specs)
#      - GND         → Ground (GND)

BH1750_ADDR = 0x23       # Default I²C address for BH1750
BH1750_CMD  = 0x10       # Continuous H-resolution mode command

bus = smbus.SMBus(1)     # Initialize I²C bus 1

def read_lux():
    """
    Reads ambient light (in lux) from the BH1750 sensor.
    """
    try:
        bus.write_byte(BH1750_ADDR, BH1750_CMD)
        time.sleep(0.180)  # Wait for measurement (120-180ms)
        data = bus.read_i2c_block_data(BH1750_ADDR, 0x00, 2)
        lux = (data[0] << 8) | data[1]
        return lux / 1.2  # Convert to lux per sensor datasheet
    except Exception as e:
        print("Error reading BH1750 sensor:", e)
        return None

# ====================================================
# Brightness Mapping Parameters
# ====================================================
MIN_BRIGHTNESS = 10      # Brightness when ambient light is high
MAX_BRIGHTNESS = 255     # Brightness when ambient light is low
LUX_MIN        = 0       # Minimum expected lux
LUX_MAX        = 1000    # Lux value at which brightness reaches MIN_BRIGHTNESS

def map_lux_to_brightness(lux):
    """
    Map ambient lux to a brightness value.
    Lower lux (darker) => higher brightness; higher lux (brighter) => lower brightness.
    """
    lux = max(LUX_MIN, min(lux, LUX_MAX))
    normalized = (lux - LUX_MIN) / (LUX_MAX - LUX_MIN)
    brightness = MAX_BRIGHTNESS - normalized * (MAX_BRIGHTNESS - MIN_BRIGHTNESS)
    return int(brightness)

# ====================================================
# LED Tree Configuration
# ====================================================
# Load LED coordinates to determine the number of LEDs.
# The CSV should contain columns: X, Y, Z.
df = pd.read_csv('coordinates.csv')
LED_COUNT = len(df)

# LED strip configuration:
LED_PIN     = 18       # GPIO pin connected to the LEDs (supports PWM)
LED_FREQ_HZ = 800000   # LED signal frequency in hertz
LED_DMA     = 10       # DMA channel to use for generating signal
LED_BRIGHTNESS = 125   # Initial brightness (this will be updated dynamically)
LED_INVERT  = False    # True if signal inversion is needed
LED_CHANNEL = 0        # Set to 0 for GPIO 18

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA,
                   LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

# ====================================================
# Color Rotation Animation
# ====================================================
# Parameters:
color_cycle_duration = 10  # Seconds for a complete cycle through hues
update_interval = 0.05     # Time (in seconds) between updates

try:
    start_time = time.time()
    while True:
        elapsed = time.time() - start_time
        # Calculate the current hue (cycles between 0 and 1)
        hue = (elapsed % color_cycle_duration) / color_cycle_duration
        # Convert HSV (hue, saturation, value) to RGB
        r, g, b = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        # Scale RGB to 0-255 range
        r, g, b = int(r * 255), int(g * 255), int(b * 255)
        current_color = Color(r, g, b)
        
        # Read ambient light and adjust brightness accordingly
        lux = read_lux()
        if lux is not None:
            brightness = map_lux_to_brightness(lux)
            strip.setBrightness(brightness)
            print("Ambient Light: {:.2f} lux  |  LED Brightness: {}".format(lux, brightness))
        else:
            print("Error reading sensor. Using default brightness.")
        
        # Set all LEDs to the current vibrant color
        for i in range(LED_COUNT):
            strip.setPixelColor(i, current_color)
        strip.show()
        
        time.sleep(update_interval)

except KeyboardInterrupt:
    # On exit, turn off all LEDs.
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
