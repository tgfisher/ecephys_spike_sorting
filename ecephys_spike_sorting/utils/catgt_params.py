"""These classes are here to support better user feedback from the pipeline.
Invalid command line parameters will fail quietly and won't produce (helpful)
errors.

These classes provide guidance, context, and will raise errors.

TODO:
 - [ ] add validation classes for cleaner init methods
 - [ ] abstact base class with "spec_string" method.

"""
from enum import IntEnum
from typing import Literal

VALID_FILTERS = ("butter", "biquad")

_BandPassFilters = Literal[VALID_FILTERS]

class _XAStreamTypes(IntEnum):
    """Valid streams for analog extractions. The 'js' in the SGLX documentation."""
    NI = 0
    OB = 1
    AP = 2

class _XAStreamIndices():
    """Valid stream indices for analog extractions. The 'ip' in the SGLX documentation.
        The tricky issue is that this is dependent on the stream type that is chosen.

        Leaving this until after the Areadne."""

    def __init__(self):
        raise NotImplementedError

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

class XtractAnalog():
    """
    E.g. extract pulse signal from analog chan (js,ip,word,thresh1(V),thresh2(V),millisec)

    -xa=0,0,2,3.0,4.5,25

    - xa: Finds positive pulses in any analog channel.
    - xia: Finds inverted pulses in any analog channel.

    Extractors xa
    -------------

    Following -xa=js,ip,word, these parameters are required:

    "js" - "input stream type" usually NI (nidq)
        NI: js = 0 (any extractor).
        OB: js = 1 (any extractor).
        AP: js = 2 (only {xd, xid} are legal)
        LF: js = 3 (not sure if can be extracted) -- TGF added

    "ip" - "input stream index"
        NI: ip = 0 (there is only one NI stream).
        OB: ip = 0 selects obx0, ip = 7 selects obx7, etc.
        AP: ip = 0 selects imec0, ip = 7 selects imec7, etc.

    "word" - Word is a zero-based channel index. It selects the 16-bit data
    word to process.

        word = -1, selects the last word in that stream. That's especially useful
        to specify the SY word at the end of a OneBox or probe stream.

    Primary threshold-1 (V).
    Optional more stringent threshold-2 (V).
    Milliseconds duration.

    If your signal looks like clean square pulses, set threshold-2 to be closer
    to baseline than threshold-1 to ignore the threshold-2 level and run more
    efficiently. For noisy signals or for non-square pulses set threshold-2 to
    be farther from baseline than theshold-1 to ensure pulses attain a desired
    deflection amplitude. Using two separate threshold levels allows detecting
    the earliest time that pulse departs from baseline (threshold-1) and
    separately testing that the deflection is great enough to be considered a
    real event and not noise (threshold-2). See Fig. 1.

    """

    def __init__(self, js: _XAStreamTypes, ip):
        """Postponing until after areadne."""
        raise NotImplementedError

