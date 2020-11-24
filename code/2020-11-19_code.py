import time
import board
import neopixel

from cedargrove_nau7802 import NAU7802

pixel = neopixel.NeoPixel(board.NEOPIXEL, 1)
pixel[0] = (4, 0, 4)

nau7802 = NAU7802(board.I2C(), address=0x2A)


while True:
    print(dir(nau7802))
    print('chip_rev:   ', hex(nau7802.chip_revision))
    print()

    pixel[0] = (4, 0, 0)
    print('reset:      ')
    flag = nau7802.reset()

    print(flag)
    pixel[0] = (0, 4, 0)

    print('chip_rev:   ', hex(nau7802.chip_revision))
    print('power_up:   ', hex(nau7802.power_up))
    print('control_1:  ', hex(nau7802.control_1))
    print('control_2:  ', hex(nau7802.control_2))
    print()

    print('enable:     ', nau7802.enable(True))
    print('chip_rev:   ', hex(nau7802.chip_revision))
    print('power_up:   ', hex(nau7802.power_up))
    print('control_1:  ', hex(nau7802.control_1))
    print('control_2:  ', hex(nau7802.control_2))
    print()

    print('read:       ', end='')
    value = nau7802.read()
    print(value, hex(value),'\n')

    print('disable:', nau7802.enable(False))
    print('device_rev: ', hex(nau7802.chip_revision))
    print('power_up:   ', hex(nau7802.power_up))
    print('control_1:  ', hex(nau7802.control_1))
    print('control_2:  ', hex(nau7802.control_2))
    print()

    pixel[0] = (4, 0, 4)

    for i in range(0, 10):
        pixel[0] = (i, 0 , i)
        time.sleep(0.75)
        pixel[0] = (0, 0, 0)
        time.sleep(0.25)
    pixel[0] = (4, 0, 4)
