import time
import smbus
from rpi_ws281x import PixelStrip, Color

BH1750_ADDR = 0x23
BH1750_CMD = 0x10 
bus = smbus.SMBus(1)

def read_lux():
    try:
        bus.write_byte(BH1750_ADDR, BH1750_CMD)
        time.sleep(0.18) 
        data = bus.read_i2c_block_data(BH1750_ADDR, 0x00, 2)
        lux = (data[0] << 8) | data[1]
        return lux / 1.2
    except:
        return None

MIN_BRIGHTNESS = 10
MAX_BRIGHTNESS = 255
LUX_MIN = 0
LUX_MAX = 1000

def map_lux_to_brightness(lux):
    if lux is None:
        return MAX_BRIGHTNESS
    lux = max(LUX_MIN, min(lux, LUX_MAX))
    norm = (lux - LUX_MIN) / (LUX_MAX - LUX_MIN)
    return int(MAX_BRIGHTNESS - norm * (MAX_BRIGHTNESS - MIN_BRIGHTNESS))

LED_COUNT = 50              
LED_PIN = 18
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 255       
LED_INVERT = False
LED_CHANNEL = 0

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ,
                   LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

print("Running ambient light test. Ctrl+C to stop.")

try:
    while True:
        lux = read_lux()
        brightness = map_lux_to_brightness(lux)
        strip.setBrightness(brightness)

        print(f"Ambient Light: {lux:.1f} lux → Brightness: {brightness}")

        for i in range(LED_COUNT):
            strip.setPixelColor(i, Color(255, 255, 255))
        strip.show()
        time.sleep(0.5)

except KeyboardInterrupt:
    for i in range(LED_COUNT):
        strip.setPixelColor(i, Color(0, 0, 0))
    strip.show()
    print("\nExiting cleanly.")
