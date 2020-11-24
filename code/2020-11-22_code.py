#2020-11-22_code.py

import time
import board
import neopixel

from cedargrove_nau7802 import NAU7802

import displayio
import terminalio
from adafruit_display_text import label
import adafruit_displayio_ssd1306

displayio.release_displays()

i2c = board.I2C()
display_bus = displayio.I2CDisplay(i2c, device_address=0x3C)
display = adafruit_displayio_ssd1306.SSD1306(display_bus, width=128, height=32)


pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel[0] = (4, 0, 4)

nau7802 = NAU7802(board.I2C(), address=0x2A)

pixel[0] = (4, 4, 0)
print('---------')
print('enable:   ', nau7802.enable(True))
#nau7802.ldo_voltage = '2V4'
nau7802.channel = 1
nau7802.gain = 128
nau7802.conversion_rate = 20
nau7802.show_status()

print('calibrate.INTERNAL:', nau7802.calibrate('INTERNAL'))
print('calibrate.OFFSET:  ', nau7802.calibrate('OFFSET'))  # only use if physical load cell is at zero

# zero
if nau7802.available:
        zero = nau7802.read()

# tare
if nau7802.available:
        tare = nau7802.read()

pixel[0] = (0, 4, 0)

while True:
    if nau7802.available:
        value = nau7802.read()
        mass = round((value - zero - tare) * (2.268 / 4800), 3)
        mass_oz = round(mass * 0.03527, 4)
        print('(%+6.3f, %+2.4f)' % (mass, mass_oz))
    else:
        print('not available')

    time.sleep(1)
