import time
from rpi_ws281x import PixelStrip, Color

LED_COUNT = 50
LED_PIN = 18       # GPIO pin (18 is PWM0)
LED_FREQ_HZ = 800000
LED_DMA = 10
LED_BRIGHTNESS = 128
LED_INVERT = False
LED_CHANNEL = 0

strip = PixelStrip(LED_COUNT, LED_PIN, LED_FREQ_HZ, LED_DMA, LED_INVERT, LED_BRIGHTNESS, LED_CHANNEL)
strip.begin()

for i in range(LED_COUNT):
    strip.setPixelColor(i, Color(255, 255, 255))  # White
    strip.show()
    time.sleep(0.1)

print("All LEDs should be on!")
