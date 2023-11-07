"""These classes are here to support better user feedback from the pipeline.
Invalid command line parameters will fail quietly and won't produce (helpful)
errors.

These classes provide guidance, context, and will raise errors.

TODO:
 - [ ] add validation classes for cleaner init methods
 - [ ] abstact base class with "spec_string" method.

"""
from typing import Literal

VALID_FILTERS = ("butter", "biquad")
_BandPassFilters = Literal[VALID_FILTERS]

def build_flags_str(cmd_flags):
    if cmd_flags:
        return "-"+" -".join(cmd_flags)
    else:
        return ""

def build_pvp_str(pvp_flags):
    if pvp_flags:
        str_list = []
        for param, val in pvp_flags.items():
            if isinstance(val, str):
                str_list.append(f"{param}={val}")
            else:
                for v in val:
                    str_list.append(f"{param}={v}")
        return build_flags_str(str_list)
    else:
        return ""

class BandPassFilt:
    def __init__( self, filter_type, order, high_pass, low_pass ):
        self.filter = filter_type
        self.order = order
        self.high_pass = high_pass # must be set first
        self.low_pass = low_pass

    @property
    def filter(self):
        return self._filter

    @filter.setter
    def filter(self, filt: _BandPassFilters):
        lowfilt = filt.lower()
        if lowfilt not in VALID_FILTERS:
            filts_options = " or ".join([f"'{f}'" for f in VALID_FILTERS])
            raise ValueError(f"Filter type '{filt}' is not supported. Choose {filts_options}.")
        else:
            self._filter = lowfilt

    @property
    def order(self):
        return self._order

    @order.setter
    def order(self, val):
        val = float(val)
        if self.filter == "biquad":
            assert val == 2, f"biquad filter order must be 2. Provided {val}"
            self._order = 2
        elif self.filter == "butter":
            self._order = val

    @property
    def high_pass(self):
        return self._high_pass

    @high_pass.setter
    def high_pass(self, hp_hz):
        hp_hz = float(hp_hz)
        try:
            if self.low_pass <= hp_hz:
                raise ValueError("The high_pass value must be below low_pass.")
            else:
                self._high_pass = self._verify_bandpass(hp_hz)
        except AttributeError:
            self._high_pass = self._verify_bandpass(hp_hz)

    @property
    def low_pass(self):
        return self._low_pass

    @low_pass.setter
    def low_pass(self, lp_hz):
        lp_hz = float(lp_hz)
        if lp_hz <= self.high_pass:
            raise ValueError("The low_pass value must be above high_pass.")
        else:
            self._low_pass = self._verify_bandpass(lp_hz)

    def _verify_bandpass(self, hz):
        try:
            return float(hz)
        except ValueError:
            raise ValueError("Bandpass frequency specs must be convert to float.")

    @property
    def spec_str(self):
        return f"{self.filter},{self.order},{self.high_pass},{self.low_pass}"

class GFix():
    def __init__(self, min_amp, min_slope, surr_nois_amp):
        self.min_amp = min_amp
        self.min_slope = min_slope
        self.surr_noise_amp = surr_nois_amp

    @property
    def min_amp(self):
        """The min_amp property."""
        return self._min_amp

    @min_amp.setter
    def min_amp(self, value):
        self._min_amp = self._valid_number(value, "amplitude")

    @property
    def min_slope(self):
        """The min_slope property."""
        return self._min_slope

    @min_slope.setter
    def min_slope(self, value):
        self._min_slope = self._valid_number(value, "slope")

    @property
    def surr_noise_amp(self):
        """The surr_noise_amp property."""
        return self._surr_noise_amp

    @surr_noise_amp.setter
    def surr_noise_amp(self, value):
        self._surr_noise_amp = self._valid_number(value, "amplitude")

    @property
    def spec_str(self):
        return f"{self.min_amp},{self.min_slope},{self.surr_noise_amp}"

    def _valid_number(self, val, kind=""):
        try:
            return float(val)
        except ValueError:
            raise ValueError(f"A {kind} value must convert to float.")
