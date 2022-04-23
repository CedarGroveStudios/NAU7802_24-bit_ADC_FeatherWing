# SPDX-FileCopyrightText: 2022 Cedar Grove Maker Studios
# SPDX-License-Identifier: MIT

# cedargrove_fake_nau7802.py  2022-04-23 v1.5  Cedar Grove Maker Studios

# A fake device driver library that simulates the CedarGrove NAU7802 24-bit
#   ADC FeatherWing, used for code testing without a connected wing.

import time
import random


class LDOVoltage:
    LDO_3V0 = 0x5  # LDO 3.0 volts; _CTRL1[5:3] = 5
    LDO_2V7 = 0x6  # LDO 2.7 volts; _CTRL1[5:3] = 6
    LDO_2V4 = 0x7  # LDO 2.4 volts; _CTRL1[5:3] = 7


class Gain:
    GAIN_X1 = 0x0  # Gain X1; _CTRL1[2:0] = 0 (chip default)
    GAIN_X2 = 0x1  # Gain X1; _CTRL1[2:0] = 1
    GAIN_X4 = 0x2  # Gain X1; _CTRL1[2:0] = 2
    GAIN_X8 = 0x3  # Gain X1; _CTRL1[2:0] = 3
    GAIN_X16 = 0x4  # Gain X1; _CTRL1[2:0] = 4
    GAIN_X32 = 0x5  # Gain X1; _CTRL1[2:0] = 5
    GAIN_X64 = 0x6  # Gain X1; _CTRL1[2:0] = 6
    GAIN_X128 = 0x7  # Gain X1; _CTRL1[2:0] = 7


class ConversionRate:
    RATE_10SPS = 0x0  #  10 samples/sec; _CTRL2[6:4] = 0 (chip default)
    RATE_20SPS = 0x1  #  20 samples/sec; _CTRL2[6:4] = 1
    RATE_40SPS = 0x2  #  40 samples/sec; _CTRL2[6:4] = 2
    RATE_80SPS = 0x3  #  80 samples/sec; _CTRL2[6:4] = 3
    RATE_320SPS = 0x7  # 320 samples/sec; _CTRL2[6:4] = 7


class CalibrationMode:
    INTERNAL = 0x0  # Offset Calibration Internal; _CTRL2[1:0] = 0 (chip default)
    OFFSET = 0x2  # Offset Calibration System;   _CTRL2[1:0] = 2
    GAIN = 0x3  # Gain   Calibration System;   _CTRL2[1:0] = 3


class FakeNAU7802:
    def __init__(self, i2c_bus, address=0x2A, active_channels=1):
        """Instantiate NAU7802; LDO 3v0 volts, gain 128, 10 samples per second
        conversion rate, disabled ADC chopper clock, low ESR caps, and PGA output
        stabilizer cap if in single channel mode. Returns True if successful."""
        # self.i2c_device = I2CDevice(i2c_bus, address)
        if not self.reset():
            raise RuntimeError("NAU7802 device could not be reset")
            return
        if not self.enable(True):
            raise RuntimeError("NAU7802 device could not be enabled")
            return
        self.ldo_voltage = "3V0"  # 3.0-volt internal analog power (AVDD)
        self._pu_ldo_source = True  # Internal analog power (AVDD)
        self.gain = 128  # X128
        self._c2_conv_rate = ConversionRate.RATE_10SPS  # 10 SPS; default
        self._adc_chop_clock = 0x3  # 0x3 = Disable ADC chopper clock
        self._pga_ldo_mode = 0x0  # 0x0 = Use low ESR capacitors
        self._act_channels = active_channels
        self._pc_cap_enable = (
            0x1  # 0x1 = Enable PGA out stabilizer cap for single channel use
        )
        if self._act_channels == 2:
            self._pc_cap_enable = (
                0x0  # 0x0 = Disable PGA out stabilizer cap for dual channel use
            )

    @property
    def chip_revision(self):
        """The chip revision code."""
        self._rev_id = "15"
        return self._rev_id

    @property
    def channel(self):
        """Selected channel number (1 or 2)."""
        return self._c2_chan_select + 1

    @channel.setter
    def channel(self, chan=1):
        """Select the active channel. Valid channel numbers are 1 and 2.
        Analog multiplexer settling time was emperically determined to be
        approximately 400ms at 10SPS, 200ms at 20SPS, 100ms at 40SPS,
        50ms at 80SPS, and 20ms at 320SPS."""
        if chan == 1:
            self._c2_chan_select = 0x0
            time.sleep(0.400)  # 400ms settling time for 10SPS
        elif chan == 2 and self._act_channels == 2:
            self._c2_chan_select = 0x1
            time.sleep(0.400)  # 400ms settling time for 10SPS
        else:
            raise ValueError("Invalid Channel Number")
            return
        return

    @property
    def ldo_voltage(self):
        """Representation of the LDO voltage value."""
        return self._ldo_voltage

    @ldo_voltage.setter
    def ldo_voltage(self, voltage="EXTERNAL"):
        """Select the LDO Voltage. Valid voltages are '2V4', '2V7', '3V0'."""
        if not ("LDO_" + voltage in dir(LDOVoltage)):
            raise ValueError("Invalid LDO Voltage")
            return
        self._ldo_voltage = voltage
        if self._ldo_voltage == "2V4":
            self._c1_vldo_volts = LDOVoltage.LDO_2V4
        elif self._ldo_voltage == "2V7":
            self._c1_vldo_volts = LDOVoltage.LDO_2V7
        elif self._ldo_voltage == "3V0":
            self._c1_vldo_volts = LDOVoltage.LDO_3V0
        return

    @property
    def gain(self):
        """The programmable amplifier (PGA) gain factor."""
        return self._gain

    @gain.setter
    def gain(self, factor=1):
        """Select PGA gain factor. Valid values are '1, 2, 4, 8, 16, 32, 64,
        and 128."""
        if not ("GAIN_X" + str(factor) in dir(Gain)):
            raise ValueError("Invalid Gain Factor")
            return
        self._gain = factor
        if self._gain == 1:
            self._c1_gains = Gain.GAIN_X1
        elif self._gain == 2:
            self._c1_gains = Gain.GAIN_X2
        elif self._gain == 4:
            self._c1_gains = Gain.GAIN_X4
        elif self._gain == 8:
            self._c1_gains = Gain.GAIN_X8
        elif self._gain == 16:
            self._c1_gains = Gain.GAIN_X16
        elif self._gain == 32:
            self._c1_gains = Gain.GAIN_X32
        elif self._gain == 64:
            self._c1_gains = Gain.GAIN_X64
        elif self._gain == 128:
            self._c1_gains = Gain.GAIN_X128
        return

    def enable(self, power=True):
        """Enable(start) or disable(stop) the internal analog and digital
        systems power. Enable = True; Disable (low power) = False. Returns
        True when enabled; False when disabled."""
        self._enable = power
        if self._enable:
            time.sleep(0.750)  # Wait 750ms; minimum 400ms
            return True
        time.sleep(0.010)  # Wait 10ms (200us minimum)
        return False

    def available(self):
        """Read the ADC data-ready status. True when data is available; False when
        ADC data is unavailable."""
        return True

    def read(self):
        """Reads the 24-bit ADC data. Returns a signed integer value with
        24-bit resolution. Assumes that the ADC data-ready bit was checked
        to be True."""
        self._adc_out = random.randrange(0, 16384)
        return self._adc_out

    def reset(self):
        """Resets all device registers and enables digital system power.
        Returns the power ready status bit value: True when system is ready;
        False when system not ready for use."""
        time.sleep(0.100)  # Wait 100ms; 10ms minimum
        time.sleep(0.750)  # Wait 750ms; 400ms minimum
        return True

    def calibrate(self, mode="INTERNAL"):
        """Perform the calibration procedure. Valid calibration modes
        are 'INTERNAL', 'OFFSET', and 'GAIN'. True if successful."""
        if not (mode in dir(CalibrationMode)):
            raise ValueError("Invalid Calibration Mode")
            return
        self._calib_mode = mode
        if self._calib_mode == "INTERNAL":  # Internal PGA offset (zero setting)
            self._c2_cal_mode = CalibrationMode.INTERNAL
        elif self._calib_mode == "OFFSET":  # External PGA offset (zero setting)
            self._c2_cal_mode = CalibrationMode.OFFSET
        elif self._calib_mode == "GAIN":  # External PGA full-scale gain setting
            self._c2_cal_mode = CalibrationMode.GAIN
        time.sleep(0.010)  # 10ms
        return True
