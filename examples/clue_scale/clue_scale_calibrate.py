# Clue Scale Calibration
# Cedar Grove NAU7802 FeatherWing example
# 2020-12-23 v01 Cedar Grove Studios

import board
import time
from   adafruit_clue                  import clue
import displayio
from   cedargrove_nau7802 import NAU7802

clue.pixel[0] = (16, 0, 16)  # Set status indicator to purple during instantiation phase

DEFAULT_CHAN =   1  # Select load cell channel input; channel A=1, channel B=2
SAMPLE_AVG   = 100  # Number of sample values to average
DEFAULT_GAIN =  64  # Default gain for internal PGA

# Instantiate 24-bit load sensor ADC
nau7802 = NAU7802(board.I2C(), address=0x2A, active_channels=2)

def zero_channel():
    # Initiate internal calibration for current channel; return raw zero offset value
    # Use when scale is started, a new channel is selected, or to adjust for measurement drift
    # Remove weight and tare from load cell before executing
    print('channel %1d calibrate.INTERNAL: %5s'
          % (nau7802.channel, nau7802.calibrate('INTERNAL')))
    print('channel %1d calibrate.OFFSET:   %5s'
          % (nau7802.channel, nau7802.calibrate('OFFSET')))
    zero_offset = read(100)  # Read average of 100 samples to establish zero offset
    print('...channel zeroed')
    return zero_offset

def select_channel(channel=1):
    # Selects a channel for reading.
    nau7802.channel = channel
    print('channel %1d selected' % (nau7802.channel))
    return

def read(samples=100):
    # Read and average consecutive raw sample values; return average raw value
    sum = 0
    for i in range(0, samples):
        if nau7802.available:
            sum = sum + nau7802.read()
    return int(sum / samples)

# Instantiate and calibrate load cell inputs
print('*** Instantiate and calibrate load cells')
clue.pixel[0] = (16, 16, 0)  # Set status indicator to yellow
print('    enable NAU7802 digital and analog power: %5s' % (nau7802.enable(True)))

nau7802.gain    = DEFAULT_GAIN        # Use default gain
nau7802.channel = DEFAULT_CHAN        # Set to default channel
zero = zero_channel()                 # Re-calibrate and get raw zero offset value
clue.pixel[0] = (0, 16, 0)            # Set status indicator to green
clue.play_tone(1660, 0.15)
clue.play_tone(1440, 0.15)

print("Place the calibration weight on the Chan_A load cell")
print("To re-zero the load cell, remove the weight and press B")

### Main loop: Read load cell and display raw value
#     Monitor Zeroing button
while True:
    value   = read(SAMPLE_AVG)
    print('   raw value:', value, hex(value))
    time.sleep(0.1)

    if clue.button_b:
        # Zero and recalibrate NAU7802 chip
        clue.play_tone(1660, 0.3)
        clue.pixel[0] = (16, 0, 0)
        zero = zero_channel()
        while clue.button_b:
            time.sleep(0.1)
        clue.pixel[0] = (0, 16, 0)
        clue.play_tone(1440, 0.5)
    pass
