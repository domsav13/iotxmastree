import time
import board
import neopixel

LED_COUNT = 50      # Number of LEDs in the strip
PIN = board.D18     # GPIO pin (must support PWM, GPIO18 is common)
BRIGHTNESS = 0.5    # Brightness (0.0 to 1.0)

pixels = neopixel.NeoPixel(PIN, LED_COUNT, brightness=BRIGHTNESS, auto_write=False)

def light_next_led(index):
    if index < LED_COUNT:
        pixels[index] = (255, 255, 255)  # White color
        pixels.show()
        print(f"LED {index + 1} lit")

def main():
    current_led = 0
    
    try:
        while current_led < LED_COUNT:
            input("Press Enter to light the next LED...")
            light_next_led(current_led)
            current_led += 1
        print("All LEDs are lit!")
    
    except KeyboardInterrupt:
        pixels.fill((0, 0, 0))  # Turn off LEDs
        pixels.show()
        print("\nLEDs turned off. Exiting...")

if __name__ == "__main__":
    main()
