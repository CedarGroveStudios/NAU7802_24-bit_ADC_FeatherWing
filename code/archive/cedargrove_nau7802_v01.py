# cedargrove_nau7802.py
# 2020-11-23 v01.0
# device driver for the CedarGrove NAU7802 24-bit ADC FeatherWing

import time
import struct
from micropython import const

from adafruit_bus_device.i2c_device import I2CDevice
from adafruit_register.i2c_struct   import ROUnaryStruct
from adafruit_register.i2c_struct   import UnaryStruct
from adafruit_register.i2c_bits     import RWBits
from adafruit_register.i2c_bits     import ROBits
from adafruit_register.i2c_bit      import RWBit
from adafruit_register.i2c_bit      import ROBit

# DEVICE REGISTER MAP
_PU_CTRL  = const(0x00)  # Power-Up Control              RW
_CTRL1    = const(0x01)  # Control 1                     RW
_CTRL2    = const(0x02)  # Control 2                     RW
_OCAL1_B2 = const(0x03)  # CH1 OFFSET Calibration[23:16] RW
_OCAL1_B1 = const(0x04)  # CH1 OFFSET Calibration[15: 8] RW
_OCAL1_B0 = const(0x05)  # CH1 OFFSET Calibration[ 7: 0] RW
_GCAL1_B3 = const(0x06)  # CH1 GAIN Calibration[31:24]   RW
_GCAL1_B2 = const(0x07)  # CH1 GAIN Calibration[23:16]   RW
_GCAL1_B1 = const(0x08)  # CH1 GAIN Calibration[15: 8]   RW
_GCAL1_B0 = const(0x09)  # CH1 GAIN Calibration[ 7: 0]   RW
_OCAL2_B2 = const(0x0A)  # CH2 OFFSET Calibration[23:16] RW
_OCAL2_B1 = const(0x0B)  # CH2 OFFSET Calibration[16: 8] RW
_OCAL2_B0 = const(0x0C)  # CH2 OFFSET Calibration[ 7: 0] RW
_GCAL2_B3 = const(0x0D)  # CH2 GAIN Calibration[31:24]   RW
_GCAL2_B2 = const(0x0E)  # CH2 GAIN Calibration[23:16]   RW
_GCAL2_B1 = const(0x0F)  # CH2 GAIN Calibration[15: 8]   RW
_GCAL2_B0 = const(0x10)  # CH2 GAIN Calibration[ 7: 0]   RW
_I2C_CTL  = const(0x11)  # I2C Control                   RW
_ADCO_B2  = const(0x12)  # ADC_OUT[23:16]                R-
_ADCO_B1  = const(0x13)  # ADC_OUT[16: 8]                R-
_ADCO_B0  = const(0x14)  # ADC_OUT[ 7: 0]                R-
_OTP_B1   = const(0x15)  # OTP[15: 8]                    R-
_ADC      = const(0x15)  # ADC Control                   -W
_OTP_B0   = const(0x16)  # OTP[ 7: 0]                    R-
_PGA      = const(0x1B)  # Programmable Gain Amplifier   RW
_PWR_CTRL = const(0x1C)  # Power Control                 RW
_REV_ID   = const(0x1F)  # Chip Revision ID              R-

class LDOVoltage:
    LDO_4V5 = const(0x0)  # LDO 4.5 volts; _CTRL1[5:3] = 0 (default)
    LDO_4V2 = const(0x1)  # LDO 4.2 volts; _CTRL1[5:3] = 1
    LDO_3V9 = const(0x2)  # LDO 3.9 volts; _CTRL1[5:3] = 2
    LDO_3V6 = const(0x3)  # LDO 3.6 volts; _CTRL1[5:3] = 3
    LDO_3V3 = const(0x4)  # LDO 3.3 volts; _CTRL1[5:3] = 4
    LDO_3V0 = const(0x5)  # LDO 3.0 volts; _CTRL1[5:3] = 5
    LDO_2V7 = const(0x6)  # LDO 2.7 volts; _CTRL1[5:3] = 6
    LDO_2V4 = const(0x7)  # LDO 2.4 volts; _CTRL1[5:3] = 7
    LDO_EXT = const(0x0)  # External LDO; _PU_AVDDS[0x7]; 0 for external source (default)

class Gain:
    GAIN_X1   = const(0x0)  # Gain X1; _CTRL1[2:0] = 0 (default)
    GAIN_X2   = const(0x1)  # Gain X1; _CTRL1[2:0] = 1
    GAIN_X4   = const(0x2)  # Gain X1; _CTRL1[2:0] = 2
    GAIN_X8   = const(0x3)  # Gain X1; _CTRL1[2:0] = 3
    GAIN_X16  = const(0x4)  # Gain X1; _CTRL1[2:0] = 4
    GAIN_X32  = const(0x5)  # Gain X1; _CTRL1[2:0] = 5
    GAIN_X64  = const(0x6)  # Gain X1; _CTRL1[2:0] = 6
    GAIN_X128 = const(0x7)  # Gain X1; _CTRL1[2:0] = 7

class ConversionRate:
    RATE_10SPS  = const(0x0)  #  10 samples/sec; _CTRL2[6:4] = 0 (default)
    RATE_20SPS  = const(0x1)  #  20 samples/sec; _CTRL2[6:4] = 1
    RATE_40SPS  = const(0x2)  #  40 samples/sec; _CTRL2[6:4] = 2
    RATE_80SPS  = const(0x3)  #  80 samples/sec; _CTRL2[6:4] = 3
    RATE_320SPS = const(0x7)  # 320 samples/sec; _CTRL2[6:4] = 7

class CalibrationMode:
    INTERNAL = const(0x0)  # Offset Calibration Internal; _CTRL2[1:0] = 0 (default)
    OFFSET   = const(0x2)  # Offset Calibration System;   _CTRL2[1:0] = 2
    GAIN     = const(0x3)  # Gain   Calibration System;   _CTRL2[1:0] = 3

class NAU7802:
    def __init__(self, i2c_bus, address=0x2A):
        """ Instantiate NAU7802; LDO 3v0 volts, gain 128, 10 samples per second
        conversion rate, disabled chopper clock, low ESR caps, and no PGA output
        stabilizer cap. Returns True if successful."""
        self.i2c_device = I2CDevice(i2c_bus, address)
        if not self.reset():
            return False  # throw an error instead
        if not self.enable(True):
            return False  # throw an error instead
        self.ldo_voltage     = '3V0'  # 3.0 volts
        self.gain            =  128   # X128
        self.conversion_rate =   10   # 10 SPS
        self._adc_chop_clock =  0x3   # 0x3 = Disable chopper clock
        self._pga_ldo_mode   =  0x0   # 0x0 = Use low ESR capacitors
        #self._pc_cap_enable  =  0x1   # 0x1 = Enable PGA out stabilizer cap for single channel use
        self._pc_cap_enable  =  0x0   # 0x0 = Disable PGA out stabilizer cap for dual channel use

        #self._i2c = 0x02  # enable temp sensor as input
        #self._pga = 0x01  # disable chopper

    # DEFINE I2C DEVICE BITS, NYBBLES, BYTES, AND REGISTERS
    _rev_id         = ROBits(4, _REV_ID, 0, 1, False)  # Chip Revision                         R-
    _pu             =   UnaryStruct(_PU_CTRL, ">B")    # Power-Up Register
    _pu_reg_reset   = RWBit(_PU_CTRL, 0, 1, False)     # Register Reset                  (RR)  RW
    _pu_digital     = RWBit(_PU_CTRL, 1, 1, False)     # Power-Up Digital Circuit        (PUD) RW
    _pu_analog      = RWBit(_PU_CTRL, 2, 1, False)     # Power-Up Analog Circuit         (PUA) RW
    _pu_ready       = ROBit(_PU_CTRL, 3, 1, False)     # Power-Up Ready Status           (PUR) R-
    _pu_cycle_start = RWBit(_PU_CTRL, 4, 1, False)     # Power-Up Conversion Cycle Start  (CS) RW
    _pu_cycle_ready = ROBit(_PU_CTRL, 5, 1, False)     # Power-Up Cycle Ready             (CR) R-
    _pu_ldo_source  = RWBit(_PU_CTRL, 7, 1, False)     # Power-Up AVDD Source           (ADDS) RW
    _c1             =   UnaryStruct(_CTRL1, ">B")      # Control_1 Register
    _c1_gains       = RWBits(3, _CTRL1, 0, 1, False)   # Control_1 Gain                (GAINS) RW
    _c1_vldo_volts  = RWBits(3, _CTRL1, 3, 1, False)   # Control_1 LDO Voltage          (VLDO) RW
    _c2             =   UnaryStruct(_CTRL2, ">B")      # Control_2 Register
    _c2_cal_mode    = RWBits(2, _CTRL2, 0, 1, False)   # Control_2 Calibration Mode   (CALMOD) RW
    _c2_cal_start   = RWBit(_CTRL2, 2, 1, False)       # Control_2 Calibration Start    (CALS) RW
    _c2_cal_error   = RWBit(_CTRL2, 3, 1, False)       # Control_2 Calibration Error (CAL_ERR) RW
    _c2_conv_rate   = RWBits(3, _CTRL2, 4, 1, False)   # Control_2 Conversion Rate       (CRS) RW
    _c2_chan_select = RWBit(_CTRL2, 7, 1, False)       # Control_2 Channel Select        (CHS) RW
    _adc_out_2      = ROUnaryStruct(_ADCO_B2, ">B")    # ADC Result Output              MSByte R-
    _adc_out_1      = ROUnaryStruct(_ADCO_B1, ">B")    # ADC Result Output            MidSByte R-
    _adc_out_0      = ROUnaryStruct(_ADCO_B0, ">B")    # ADC Result Output              LSByte R-
    _adc            =   UnaryStruct(_ADC, ">B")        # ADC Register
    _adc_chop_clock = RWBits(2, _ADC, 4, 1, False)     # ADC Chopper Clock Frequency Select    -W
    _pga            =   UnaryStruct(_PGA, ">B")        # PGA Register
    _pga_ldo_mode   = RWBit(_PGA, 6, 1, False)         # PGA Stability/Accuracy Mode (LDOMODE) RW
    _pc_cap_enable  = RWBit(_PWR_CTRL, 7, 1, False)    # Power_Ctrl PGA Capacitor (PGA_CAP_EN) RW

    @property
    def chip_revision(self):
        """The chip revision code."""
        return self._rev_id

    @property
    def channel(self):
        "Selected channel number (1 or 2)."
        return self._c2_chan_select + 1
    @channel.setter
    def channel(self, chan=1):
        """Select the active channel. Valid channel numbers are 1 and 2."""
        if chan == 1:
            self._c2_chan_select = 0x0
        elif chan == 2:
            self._c2_chan_select = 0x1
        else:
            raise ValueError("Invalid Channel Number")
            return
        return

    @property
    def ldo_voltage(self):
        """Representation of the LDO voltage value."""
        return self._ldo_voltage
    @ldo_voltage.setter
    def ldo_voltage(self, voltage='EXTERNAL'):
        """Select the LDO Voltage. Valid voltages are '2V4', '2V7', '3V0',
        '3V3', '3V6', '3V9', '4V2', '4V5', 'EXT'."""
        if not ('LDO_' + voltage in dir(LDOVoltage)):
            raise ValueError("Invalid LDO Voltage")
            return
        self._ldo_voltage = voltage
        if self._ldo_voltage == '2V4':
            self._c1_vldo_volts = LDOVoltage.LDO_2V4
        elif self._ldo_voltage == '2V7':
            self._c1_vldo_volts = LDOVoltage.LDO_2V7
        elif self._ldo_voltage == '3V0':
            self._c1_vldo_volts = LDOVoltage.LDO_3V0
        elif self._ldo_voltage == '3V3':
            self._c1_vldo_volts = LDOVoltage.LDO_3V3
        elif self._ldo_voltage == '3V6':
            self._c1_vldo_volts = LDOVoltage.LDO_3V6
        elif self._ldo_voltage == '3V9':
            self._c1_vldo_volts = LDOVoltage.LDO_3V9
        elif self._ldo_voltage == '4V2':
            self._c1_vldo_volts = LDOVoltage.LDO_4V2
        elif self._ldo_voltage == '4V5':
            self._c1_vldo_volts = LDOVoltage.LDO_4V5

        if self._ldo_voltage == 'EXT':
            self._pu_ldo_source = False
        else:
            self._pu_ldo_source = True
        return

    @property
    def gain(self):
        """The programmable amplifier (PGA) gain factor."""
        return self._gain
    @gain.setter
    def gain(self, factor=1):
        """Select PGA gain factor. Valid values are '1, 2, 4, 8, 16, 32, 64,
        and 128."""
        if not ('GAIN_X' + str(factor) in dir(Gain)):
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

    @property
    def conversion_rate(self):
        """The conversion rate."""
        return self._conv_rate
    @conversion_rate.setter
    def conversion_rate(self, rate=10):
        """Select the conversion rate value. Valid rates are 10, 20, 40, 80, and 320
        samples per second."""
        if not ('RATE_' + str(rate) + 'SPS' in dir(ConversionRate)):
            raise ValueError("Invalid Conversion Rate")
            return
        self._conv_rate = rate
        if self._conv_rate == 10:
            self._c2_conv_rate = ConversionRate.RATE_10SPS
        elif self._conv_rate == 20:
            self._c2_conv_rate = ConversionRate.RATE_20SPS
        elif self._conv_rate == 40:
            self._c2_conv_rate = ConversionRate.RATE_40SPS
        elif self._conv_rate == 80:
            self._c2_conv_rate = ConversionRate.RATE_80SPS
        elif self._conv_rate == 320:
            self._c2_conv_rate = ConversionRate.RATE_320SPS
        return

    def enable(self, power=True):
        """Enable(start) or disable(stop) the internal analog and digital
        systems power. Enable = True; Disable (low power) = False. Returns
        True when enabled; False when disabled."""
        self._enable = power
        if self._enable:
            self._pu_analog  = True
            self._pu_digital = True
            time.sleep(0.750)  # Wait 750ms; minimum 400ms
            self._pu_start   = True  # Start acquisition system cycling
            return self._pu_ready
        self._pu_analog  = False
        self._pu_digital = False
        time.sleep(0.010)  # Wait 10ms (200us minimum)
        return False

    def available(self):
        """Read the ADC data-ready status. True when data is available; False when
        ADC data is unavailable."""
        return self._pu_cycle_ready

    def read(self):
        """Reads the 24-bit ADC data. Returns a signed integer value with
        24-bit resolution. Assumes that the ADC data-ready bit was checked
        to be True. """
        adc = self._adc_out_2  << 24         # [31:24] << MSByte
        adc = adc | (self._adc_out_1 << 16)  # [23:16] << MidSByte
        adc = adc | (self._adc_out_0 << 8)   # [15: 8] << LSByte
        adc   = adc.to_bytes(4, "big")  # Pack to 4-byte (32-bit) structure
        value = struct.unpack(">i", adc)[0]  # Unpack as 4-byte signed integer
        self._adc_out = value / 128  # Restore to 24-bit signed integer value
        return self._adc_out

    def reset(self):
        """ Resets all device registers and enables digital system power.
        Returns the power ready status bit value: True when system is ready;
        False when system not ready for use."""
        self._pu_reg_reset = True  # Reset all registers)
        time.sleep(0.100)          # Wait 100ms; 10ms minimum
        self._pu_reg_reset = False
        self._pu_digital   = True
        time.sleep(0.750)  # Wait 750ms; 400ms minimum
        return self._pu_ready

    def calibrate(self, mode='INTERNAL'):
        """ Perform the calibration procedure. Valid calibration modes
        are 'INTERNAL', 'OFFSET', and 'GAIN'. True if successful."""
        if not (mode in dir(CalibrationMode)):
            raise ValueError("Invalid Calibration Mode")
            return
        self._calib_mode = mode
        if self._calib_mode == 'INTERNAL':
            self._c2_cal_mode = CalibrationMode.INTERNAL
        elif self._calib_mode == 'OFFSET':
            self._c2_cal_mode = CalibrationMode.OFFSET
        elif self._calib_mode == 'GAIN':
            self._c2_cal_mode = CalibrationMode.GAIN
        self._c2_cal_start = True
        while self._c2_cal_start:
            time.sleep(1.010)  # 10ms
        return not self._c2_cal_error

    def show_status(self):
        """Print selected settings and register contents to the REPL.
        Useful for debugging."""
        print('chip_rev ldo_volts conv_rate gain channel')
        print('-------- --------- --------- ---- -------')
        print('     0x%1X       %3s    %3dSPS %3dX       %1d' % (self.chip_revision,
              self.ldo_voltage, self.conversion_rate, self.gain, self.channel))
        print('-------- --------- --------- ---- -------')

        print('pu_reg ctrl_1 ctrl_2 adc_reg pga_reg')
        print('------ ------ ------ ------- -------')
        print('  0x%02X   0x%02X   0x%02X    0x%02X    0x%02X' % (self._pu,
              self._c1, self._c2, self._adc, self._pga))
        print('------ ------ ------ ------- -------')
        return
