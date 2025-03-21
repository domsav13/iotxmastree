import time
import board
import neopixel

LED_COUNT = 50      # Number of LEDs in the strip
PIN = board.D18     # GPIO pin (must support PWM, GPIO18 is common)
BRIGHTNESS = 0.5    # Brightness (0.0 to 1.0)
DELAY = 0.1         # Delay between lighting each LED (in seconds)

pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)

def light_next_led(index):
    if index < LED_COUNT:
        pixels[index] = (255, 255, 255)  # White color
        pixels.show()
        print(f"LED {index + 1} lit")

def main():
    try:
        for current_led in range(LED_COUNT):
            light_next_led(current_led)
            time.sleep(DELAY)
        print("All LEDs are lit!")
    
    except KeyboardInterrupt:
        pixels.fill((0, 0, 0))  # Turn off LEDs
        pixels.show()
        print("\nLEDs turned off. Exiting...")

if __name__ == "__main__":
    main()
