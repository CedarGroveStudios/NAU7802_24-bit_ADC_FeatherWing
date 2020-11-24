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
    print('-------- --------- --------- ---- -------')
    print('     0x%1X       %3s    %3dSPS %3dX       %1d' % (nau7802.chip_revision,
          nau7802.ldo_voltage, nau7802.conversion_rate, nau7802.gain, nau7802.channel))
    print('-------- --------- --------- ---- -------')

    print('pu_reg ctrl_1 ctrl_2 adc_reg pga_reg')
    print('------ ------ ------ ------- -------')
    print('  0x%02X   0x%02X   0x%02X    0x%02X    0x%02X' % (nau7802.power_up_reg,
          nau7802.control_1_reg, nau7802.control_2_reg,nau7802.adc_reg, nau7802.pga_reg))
    print('------ ------ ------ ------- -------')
    pixel[0] = (0, 4, 0)

while True:
    print('---------')
    print('enable:   ', nau7802.enable(True))
    #nau7802.ldo_voltage = '2V4'
    nau7802.channel = 1
    nau7802.gain = 128
    nau7802.conversion_rate = 20
    show_status()

    print('calibrate.INTERNAL:', nau7802.calibrate('INTERNAL'))
    #print('calibrate.OFFSET:  ', nau7802.calibrate('OFFSET'))
    #while not nau7802.calibrate('GAIN'):
        #print('calibrate.GAIN:    ', nau7802.calibrate('GAIN'))

    while True:
        print('******** start conversion:', nau7802.start_conversion())
        if nau7802.available:
            value = nau7802.read()
            print('read:  %i   0x%06X' %(value, value))
            print((value, ))
        show_status()
        time.sleep(1)

    print('enable:   ', nau7802.enable(False))
    show_status()

    pixel[0] = (4, 0, 4)

    for i in range(0, 10):
        pixel[0] = (i, 0 , i)
        time.sleep(0.75)
        pixel[0] = (0, 0, 0)
        time.sleep(0.25)
    pixel[0] = (4, 0, 4)
