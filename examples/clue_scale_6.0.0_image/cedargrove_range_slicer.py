# The MIT License (MIT)

# Copyright (c) 2020 Cedar Grove Studios

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.

# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
"""
`cedargrove_range_slicer`
================================================================================
Range_Slicer 2020-10-06 v30 12:09PM (Version 3.0)
A CircuitPython class for scaling a range of input values into indexed/quantized
output values. Output slice hysteresis is used to provide dead-zone squelching.

* Author(s): Cedar Grove Studios

Implementation Notes
--------------------
** Software and Dependencies: **
  * Adafruit CircuitPython firmware for the supported boards:
    https://github.com/adafruit/circuitpython/releases
"""

__repo__ = "https://github.com/CedarGroveStudios/Range_Slicer.git"

class Slicer:
    """range_slicer helper class."""

    def __init__(self, in_min=0, in_max=65535, out_min=0, out_max=65535,
                 slice=1.0, hyst_factor=0.10, out_integer=False, debug=False):

        self._in_min = in_min            # input min/max parameters
        self._in_max = in_max
        self._out_min = out_min          # output min/max parameters
        self._out_max = out_max
        self._slice = slice              # output slice size parameter
        self._hyst_factor = hyst_factor  # hysteresis factor parameter
        self._out_integer = out_integer  # output data type parameter

        self._debug = debug              # debug parameter
        """if self._debug:
            print("*Init:", self.__class__)
            print("*Init: ", self.__dict__)"""

        self._update_param() # Establish the parameters for range_slicer helper

    @property
    def range_min(self):
        """The range input's minimum floating or integer value.
           Default is 0."""
        return self._in_min
    @range_min.setter
    def range_min(self, in_min=0):
        self._in_min = in_min
        self._update_param() # Update the parameters for range_slicer helper

    @property
    def range_max(self):
        """The range input's maximum floating or integer value.
           Default is 65535."""
        return self._in_max
    @range_max.setter
    def range_max(self, in_max=65535):
        self._in_max = in_max
        self._update_param() # Update the parameters for range_slicer helper

    @property
    def index_min(self):
        """The index output minimum value. Default is 0."""
        return self._out_min
    @index_min.setter
    def index_min(self, out_min=0):
        self._out_min = out_min
        self._update_param() # Update the parameters for range_slicer helper

    @property
    def index_max(self):
        """The index output maximum value. Default is 65535."""
        return self._out_max
    @index_max.setter
    def index_max(self, out_max=65535):
        self._out_max = out_max
        self._update_param() # Update the parameters for range_slicer helper

    @property
    def index_type(self):
        """The index output value integer data type.
           Default is False (floating)."""
        return self._out_integer
    @index_type.setter
    def index_type(self, out_integer=False):
        self._out_integer = out_integer
        self._update_param() # Update the parameters for range_slicer helper

    @property
    def slice(self):
        """The slice size value. Default is 1.0."""
        return self._slice
    @slice.setter
    def slice(self, size=1.0):
        if size <= 0:
            raise RuntimeError("Invalid Slice setting; value must be greater than zero")
        self._slice = size
        self._update_param() # Update the parameters for range_slicer helper

    @property
    def hysteresis(self):
        """The hysteresis factor value. For example, a factor of 0.50 is a
        hysteresis setting of 50%. Default is 0.10 (10%)"""
        return self._hyst_factor
    @hysteresis.setter
    def hysteresis(self, hyst_factor=0.10):
        self._hyst_factor = hyst_factor

    @property
    def debug(self):
        """The class debugging mode. Default is False."""
        return self._debug
    @debug.setter
    def debug(self, debug=False):
        self._debug = debug
        """if self._debug:
            print("*Init:", self.__class__)
            print("*Init: ", self.__dict__)"""

    """range_slicer: Determines an index (output) value from the input value.
         Returns new index value and a change flag (True/False) if the new
         index changed from the previous index. Index value can be optionally
         converted to integer data type.
         This is the primary function of the Slicer class. """
    def range_slicer(self, input=0):
        if self._out_span_dir == 1:
            idx_mapped = self._mapper(input) + self._hyst_band
            slice_num = (((idx_mapped - self._out_span_min) - ((idx_mapped - self._out_span_min) % self._slice)) / self._slice)
            slice_thresh = (slice_num * self._slice) + self._out_span_min
        else:
            idx_mapped = self._mapper(input) + self._hyst_band
            slice_num = (((idx_mapped - self._out_span_max) - ((idx_mapped - self._out_span_max) % self._slice)) / self._slice)
            slice_thresh = (slice_num * self._slice) + self._out_span_max
        upper_zone_limit = slice_thresh + (2 * self._hyst_band)
        if (idx_mapped <= upper_zone_limit and idx_mapped >= slice_thresh):
            if self._in_zone != slice_thresh:
                self._in_zone = slice_thresh
                if idx_mapped > self._old_idx_mapped:
                    self._index = slice_thresh - self._slice
                if idx_mapped < self._old_idx_mapped:
                    self._index = slice_thresh
        else:
            self._in_zone = None
            self._index = slice_thresh
        if self._out_span_min <= self._out_span_max:
            self._index = max(min(self._index, self._out_span_max), self._out_span_min)
        else:
            self._index = min(max(self._index, self._out_span_max), self._out_span_min)
        if self._index != self._old_idx_mapped:
            change_flag = True
        else:
            change_flag = False
        self._old_idx_mapped = idx_mapped
        if self._out_integer:
            return int(self._index), change_flag
        return self._index, change_flag

    """_mapper: Determines the linear output value based on the input value.
         ( y = mx + b ) """
    def _mapper(self, map_in):
        if (self._in_min == self._in_max) or (self._out_span_min == self._out_span_max):
            return self._out_span_min
        mapped = (((self._out_span_max - self._out_span_min) / (self._in_max - self._in_min))
                   * (map_in - self._in_min)) + self._out_span_min
        if self._out_span_min <= self._out_span_max:
            return max(min(mapped, self._out_span_max), self._out_span_min)
        else:
            return min(max(mapped, self._out_span_max), self._out_span_min)

    """Determines the sign of a numeric value. Zero is evaluated as a
         positive value.  """
    def _sign(self, x):
        if x >= 0:
            return 1
        else: return -1

    """ Recalculate spans and hysteresis value when parameters change. """
    def _update_param(self):
        # output span parameters
        if self._out_min > self._out_max:
            self._out_span_min = self._out_min + self._slice
            self._out_span_max = self._out_max
        else:
            self._out_span_min = self._out_min
            self._out_span_max = self._out_max + self._slice
        self._out_span = (self._out_span_max - self._out_span_min)
        self._out_span_dir = self._sign(self._out_span)
        # slice size parameter
        if self._slice <= 0:
            raise RuntimeError("Invalid Slice value; must be greater than zero")
        # hysteresis parameters: calculate hysteresis band size, reset in-zone state
        self._hyst_band = self._hyst_factor * self._slice
        self._in_zone = None
        # index parameters
        self._index = 0
        self._old_idx_mapped = 0
        return
