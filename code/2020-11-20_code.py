#2020-11-20_code.py

import time
import board
import neopixel

from cedargrove_nau7802 import NAU7802

pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel[0] = (4, 0, 4)

nau7802 = NAU7802(board.I2C(), address=0x2A)

def show_status():
    pixel[0] = (4, 0, 0)
    print('chip_rev ldo_volts conv_rate gain channel')
    print('     0x%1X       0x%1X       0x%1X  0x%1X       %1d' % (nau7802.chip_revision,
          nau7802.ldo_voltage, nau7802.conversion_rate, nau7802.gain, nau7802.channel))
    pixel[0] = (0, 4, 0)

while True:
    print('---------')
    print('enable:   ', nau7802.enable(True))
    show_status()

    print('calibrate:', nau7802.calibrate('INTERNAL'))

    value = nau7802.read()
    print('read:     ', value, hex(value))

    print('enable:   ', nau7802.enable(False))
    show_status()

    pixel[0] = (4, 0, 4)

    for i in range(0, 10):
        pixel[0] = (i, 0 , i)
        time.sleep(0.75)
        pixel[0] = (0, 0, 0)
        time.sleep(0.25)
    pixel[0] = (4, 0, 4)
