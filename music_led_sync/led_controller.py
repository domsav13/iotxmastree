import board
import neopixel
import time

# Pin and number of LEDs
LED_PIN = board.D18
NUM_LEDS = 50

pixels = neopixel.NeoPixel(LED_PIN, NUM_LEDS, brightness=0.5, auto_write=False)

def update_leds(color):
    pixels.fill(color)
    pixels.show()

def pulse_led(color, duration=0.1, pulses=5):
    for _ in range(pulses):
        pixels.fill(color)
        pixels.show()
        time.sleep(duration)
        pixels.fill((0, 0, 0))
        pixels.show()
        time.sleep(duration)
