import time
import smbus
from rpi_ws281x import PixelStrip

BH1750_ADDR = 0x23
BH1750_CMD  = 0x10
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
LUX_MIN, LUX_MAX = 0, 1000

def map_lux_to_brightness(lux):
    if lux is None:
        return MAX_BRIGHTNESS
    lux = max(LUX_MIN, min(lux, LUX_MAX))
    norm = (lux - LUX_MIN) / (LUX_MAX - LUX_MIN)
    return int(MAX_BRIGHTNESS - norm * (MAX_BRIGHTNESS - MIN_BRIGHTNESS))

_original_show = PixelStrip.show

def _patched_show(self, *args, **kwargs):
    lux = read_lux()
    br  = map_lux_to_brightness(lux)
    self.setBrightness(br)
    return _original_show(self, *args, **kwargs)

PixelStrip.show = _patched_show
