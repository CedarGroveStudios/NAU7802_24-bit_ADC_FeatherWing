#2020-11-20_code.py

import time
import board
import neopixel

from cedargrove_nau7802 import NAU7802

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
        mass = (value - zero - tare) * (2.268 / 4800)
        print((round(mass, 3), ))
    else:
        print('not available')

    time.sleep(5)
