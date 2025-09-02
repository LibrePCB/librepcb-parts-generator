"""
Configuration file, containing all available DFN configs.

"""

from typing import Any, Callable, Optional, Tuple

from entities.common import Angle, Circle, Diameter, Fill, GrabArea, Layer, Polygon, Position, Vertex, Width
from entities.package import Footprint

# Maximal lead width as a function of pitch, Table 4 in the JEDEC
# standard MO-229F, available (with registration!) from
# https://www.jedec.org/system/files/docs/MO-229F.pdf
LEAD_WIDTH = {
    0.95: 0.45,
    0.8: 0.35,
    0.65: 0.35,
    0.5: 0.30,
    0.4: 0.25,
}

# Toe and heel length as a function of pitch
# According to IPC-7351C, see slide 26 of
# http://ocipcdc.org/archive/What_is_New_in_IPC-7351C_03_11_2015.pdf
LEAD_TOE_HEEL = {
    1.00: 0.35,
    0.95: 0.35,    # not specified in standard
    0.8: 0.33,
    0.65: 0.31,
    0.50: 0.29,
    0.40: 0.27,
    0.35: 0.25,
}

# The real CadQuery types are not known statically, thus allowing any type.
StepModificationFn = Callable[[Any, Any, Any], Tuple[Any, Any]]


class DfnConfig:
    def __init__(self,
                 length: float,
                 width: float,
                 pitch: float,
                 pin_count: int,
                 height_nominal: float,
                 height_max: float,
                 lead_length: float,
                 exposed_width: float,
                 exposed_length: float,
                 keywords: str,
                 no_exp: bool = True,    # By default we create variants w/o exp
                 print_pad: bool = False,    # By default, the pad length is not in the full name
                 lead_width: Optional[float] = None,
                 name: Optional[str] = None,
                 create_date: Optional[str] = None,
                 library: Optional[str] = None,
                 pin1_corner_dx_dy: Optional[float] = None,  # Some parts have a triangular pin1 marking
                 extended_doc_fn: Optional[Callable[['DfnConfig', Callable[[str], str], Footprint], None]] = None,
                 step_modification_fn: Optional[StepModificationFn] = None,
                 ):
        self.length = length
        self.width = width
        self.pitch = pitch
        self.pin_count = pin_count
        self.height = height_max
        self.height_nominal = height_nominal

        self.exposed_width = exposed_width        # E2
        self.exposed_length = exposed_length      # D2
        self.no_exp = no_exp                      # Option with noexp

        self.lead_length = lead_length
        self.print_pad = print_pad
        if lead_width:
            self.lead_width = lead_width
        else:
            self.lead_width = LEAD_WIDTH[pitch]

        # Save toe/heel length
        try:
            self.toe_heel = LEAD_TOE_HEEL[pitch]
        except KeyError:
            raise NotImplementedError("No toe/heel length for pitch {:s}".format(pitch))

        self.keywords = keywords
        self.name = name
        self.create_date = create_date
        self.library = library or "LibrePCB_Base.lplib"

        self.extended_doc_fn = extended_doc_fn
        self.step_modification_fn = step_modification_fn


# fmt: off
JEDEC_CONFIGS = [
    # Table 6
    # Square, 1.5 x 1.5
    DfnConfig(1.5, 1.5, 0.5, 4, 0.95, 1.00, 0.55, 0.70, 0.10, 'V1515D,VBBD'),
    DfnConfig(1.5, 1.5, 0.5, 4, 0.75, 0.80, 0.55, 0.70, 0.10, 'W1515D,WBBD'),
    # Square, 2.0 x 2.0
    DfnConfig(2.0, 2.0, 0.65, 6, 0.95, 1.00, 0.30, 1.58, 0.65, 'V2020C,VCCC'),    # no nominal exp_pad
    DfnConfig(2.0, 2.0, 0.5, 4, 0.95, 1.00, 0.55, 1.20, 0.60, 'V2020D-1,VCCD-1'),
    DfnConfig(2.0, 2.0, 0.5, 4, 0.75, 0.80, 0.55, 1.20, 0.60, 'W2020D-1,WCCD-1'),
    DfnConfig(2.0, 2.0, 0.5, 6, 0.95, 1.00, 0.40, 1.75, 0.80, 'V2020D-4,VCCD-4', no_exp=False),     # no nominal exp_pad
    DfnConfig(2.0, 2.0, 0.5, 6, 0.75, 0.80, 0.40, 1.75, 0.80, 'W2020D-4,WCCD-4', no_exp=False),     # no nominal exp_pad
    DfnConfig(2.0, 2.0, 0.5, 6, 0.95, 1.00, 0.55, 1.20, 0.60, 'V2020D-2,VCCD-2'),
    DfnConfig(2.0, 2.0, 0.5, 6, 0.75, 0.80, 0.55, 1.20, 0.60, 'W2020D-2,WCCD-2'),
    DfnConfig(2.0, 2.0, 0.5, 8, 0.95, 1.00, 0.30, 1.20, 0.60, 'V2020D-3,VCCD-3'),
    # Square, 2.5 x 2.5
    DfnConfig(2.5, 2.5, 0.8, 6, 0.95, 1.00, 0.55, 1.50, 0.70, 'V2525B,VDDB'),
    DfnConfig(2.5, 2.5, 0.8, 6, 0.75, 0.80, 0.55, 1.50, 0.70, 'W2525B,WDDB'),
    DfnConfig(2.5, 2.5, 0.5, 6, 0.95, 1.00, 0.55, 1.70, 1.10, 'V2525D-1,VDDD-1'),
    DfnConfig(2.5, 2.5, 0.5, 6, 0.75, 0.80, 0.55, 1.70, 1.10, 'W2525D-1,WDDD-1'),
    DfnConfig(2.5, 2.5, 0.5, 8, 0.95, 1.00, 0.55, 1.70, 1.10, 'V2525D-2,VDDD-2'),
    DfnConfig(2.5, 2.5, 0.5, 8, 0.75, 0.80, 0.55, 1.70, 1.10, 'W2525D-2,WDDD-2'),
    # Square, 3.0 x 3.0
    DfnConfig(3.0, 3.0, 0.95, 6, 0.95, 1.00, 0.55, 1.50, 0.70, 'V3030A-1,VEEA-1'),
    DfnConfig(3.0, 3.0, 0.95, 6, 0.95, 1.00, 0.55, 1.50, 1.20, 'V3030A-2,VEEA-2', no_exp=False),
    # no_exp above, as it would be the same as the V3030A-1 without exposed pad
    DfnConfig(3.0, 3.0, 0.95, 6, 0.75, 0.80, 0.55, 1.50, 1.20, 'W3030A-2,WEEA-2'),
    DfnConfig(3.0, 3.0, 0.8, 6, 0.95, 1.00, 0.50, 2.20, 1.30, 'V3030B,VEEB'),
    DfnConfig(3.0, 3.0, 0.8, 6, 0.75, 0.80, 0.55, 2.20, 1.30, 'W3030B,WEEB'),
    DfnConfig(3.0, 3.0, 0.65, 8, 0.95, 1.00, 0.30, 2.25, 1.30, 'V3030C-1,VEEC-1'),   # no nominal exp_pad
    DfnConfig(3.0, 3.0, 0.65, 8, 0.95, 1.00, 0.40, 2.50, 1.75, 'V3030C-2,VEEC-2', no_exp=False),    # no nominal exp_pad
    DfnConfig(3.0, 3.0, 0.65, 8, 0.75, 0.80, 0.40, 2.50, 1.75, 'W3030C-2,WEEC-2', no_exp=False),    # no nominal exp_pad
    DfnConfig(3.0, 3.0, 0.5, 8, 0.95, 1.00, 0.55, 2.20, 1.60, 'V3030D-1,VEED-1'),
    DfnConfig(3.0, 3.0, 0.5, 8, 0.75, 0.80, 0.55, 2.00, 1.20, 'W3030D-1,WEED-1'),
    DfnConfig(3.0, 3.0, 0.5, 8, 0.95, 1.00, 0.40, 2.70, 1.75, 'V3030D-4,VEED-4', no_exp=False),     # no nominal exp_pad
    DfnConfig(3.0, 3.0, 0.5, 8, 0.75, 0.80, 0.40, 2.70, 1.75, 'W3030D-4,WEED-4', no_exp=False),     # no nominal exp_pad
    DfnConfig(3.0, 3.0, 0.5, 8, 0.95, 1.00, 0.55, 2.50, 1.50, 'V3030D-6,VEED-6', no_exp=False),     # no nominal exp_pad
    DfnConfig(3.0, 3.0, 0.5, 8, 0.75, 0.80, 0.55, 2.50, 1.50, 'W3030D-6,WEED-6', no_exp=False),     # no nominal exp_pad
    DfnConfig(3.0, 3.0, 0.5, 8, 0.95, 1.00, 0.45, 1.60, 1.60, 'V3030D-7,VEED-7', no_exp=False),     # no nominal pad length and exp_pad  # noqa: E501
    DfnConfig(3.0, 3.0, 0.5, 8, 0.75, 0.80, 0.45, 1.60, 1.60, 'W3030D-7,WEED-7', no_exp=False),     # no nominal pad length and exp_pad  # noqa: E501
    DfnConfig(3.0, 3.0, 0.5, 10, 0.95, 1.00, 0.55, 2.20, 1.60, 'V3030D-2,VEED-2', print_pad=True),
    DfnConfig(3.0, 3.0, 0.5, 10, 0.75, 0.80, 0.55, 2.00, 1.20, 'W3030D-2,WEED-2'),
    DfnConfig(3.0, 3.0, 0.5, 10, 0.95, 1.00, 0.30, 2.20, 1.60, 'V3030D-3,VEED-3', print_pad=True),
    DfnConfig(3.0, 3.0, 0.5, 10, 0.95, 1.00, 0.40, 2.70, 1.75, 'V3030D-5,VEED-5', no_exp=False),    # no nominal exp_pad
    DfnConfig(3.0, 3.0, 0.5, 10, 0.75, 0.80, 0.40, 2.70, 1.75, 'W3030D-5,WEED-5', no_exp=False),    # no nominal exp_pad
    # Square, 3.5 x 3.5
    DfnConfig(3.5, 3.5, 0.5, 10, 0.95, 1.00, 0.55, 2.70, 2.10, 'V3535D-1,VFFD-1'),
    DfnConfig(3.5, 3.5, 0.5, 10, 0.75, 0.80, 0.55, 2.70, 2.10, 'W3535D-1,WFFD-1'),
    DfnConfig(3.5, 3.5, 0.5, 12, 0.95, 1.00, 0.55, 2.70, 2.10, 'V3535D-2,VFFD-2'),
    DfnConfig(3.5, 3.5, 0.5, 12, 0.75, 0.80, 0.55, 2.70, 2.10, 'W3535D-2,WFFD-2'),
    # Square, 4.0 x 4.0
    DfnConfig(4.0, 4.0, 0.8, 8, 0.95, 1.00, 0.55, 3.00, 2.20, 'V4040B,VGGB'),
    DfnConfig(4.0, 4.0, 0.8, 8, 0.75, 0.80, 0.55, 3.00, 2.20, 'W4040B,WGGB'),
    DfnConfig(4.0, 4.0, 0.65, 10, 0.95, 1.00, 0.40, 3.50, 2.80, 'V4040C,VGGC', no_exp=False),   # no nominal exp_pad
    DfnConfig(4.0, 4.0, 0.65, 10, 0.75, 0.80, 0.40, 3.50, 2.80, 'W4040C,WGGC', no_exp=False),   # no nominal exp_pad
    DfnConfig(4.0, 4.0, 0.5, 10, 0.95, 1.00, 0.55, 3.20, 2.60, 'V4040D-1,VGGD-1'),
    DfnConfig(4.0, 4.0, 0.5, 10, 0.75, 0.80, 0.55, 3.00, 2.20, 'W4040D-1,WGGD-1'),
    DfnConfig(4.0, 4.0, 0.5, 12, 0.95, 1.00, 0.55, 3.20, 2.60, 'V4040D-2,VGGD-2'),
    DfnConfig(4.0, 4.0, 0.5, 12, 0.75, 0.80, 0.55, 3.00, 2.20, 'W4040D-2,WGGD-2'),
    DfnConfig(4.0, 4.0, 0.5, 14, 0.95, 1.00, 0.55, 3.20, 2.60, 'V4040D-3,VGGD-3'),
    DfnConfig(4.0, 4.0, 0.5, 14, 0.75, 0.80, 0.55, 3.00, 2.20, 'W4040D-3,WGGD-3'),
    # Square, 5.0 x 5.0
    DfnConfig(5.0, 5.0, 0.8, 8, 0.95, 1.00, 0.55, 4.00, 3.20, 'V5050B,VJJB'),
    DfnConfig(5.0, 5.0, 0.8, 8, 0.75, 0.80, 0.55, 4.00, 3.20, 'W5050B,WJJB'),
    DfnConfig(5.0, 5.0, 0.5, 16, 0.95, 1.00, 0.55, 4.20, 3.60, 'V5050D-1,VJJD-1'),
    DfnConfig(5.0, 5.0, 0.5, 16, 0.75, 0.80, 0.55, 4.00, 3.20, 'W5050D-1,WJJD-1'),
    DfnConfig(5.0, 5.0, 0.5, 18, 0.95, 1.00, 0.55, 4.20, 3.60, 'V5050D-2,VJJD-2'),
    DfnConfig(5.0, 5.0, 0.5, 18, 0.75, 0.80, 0.55, 4.00, 3.20, 'W5050D-2,WJJD-2'),
    # Table 6
    # Rectangular, Type 1, 2.0 x 2.5
    DfnConfig(2.0, 2.5, 0.8, 4, 0.95, 1.00, 0.55, 1.00, 0.70, 'V2025B,VCDB'),
    DfnConfig(2.0, 2.5, 0.8, 4, 0.75, 0.80, 0.55, 1.00, 0.70, 'W2025B,WCDB'),
    DfnConfig(2.0, 2.5, 0.5, 6, 0.95, 1.00, 0.55, 1.00, 0.70, 'V2025D-1,VCDD-1'),
    DfnConfig(2.0, 2.5, 0.5, 6, 0.75, 0.80, 0.55, 1.00, 0.70, 'W2025D-1,WCDD-1'),
    DfnConfig(2.0, 2.5, 0.5, 8, 0.95, 1.00, 0.55, 1.10, 0.80, 'V2025D-2,VCDD-2'),    # no nominal exp_pad
    DfnConfig(2.0, 2.5, 0.5, 8, 0.75, 0.80, 0.55, 1.10, 0.80, 'W2025D-2,WCDD-2'),    # no nominal exp_pad
    # Rectangular, Type 1, 2.0 x 3.0
    DfnConfig(2.0, 3.0, 0.5, 6, 0.95, 1.00, 0.40, 1.00, 1.20, 'V2030D-1,VCED-1', no_exp=False),    # no nominal exp_pad
    DfnConfig(2.0, 3.0, 0.5, 6, 0.75, 0.80, 0.40, 1.00, 1.20, 'W2030D-1,WCED-1', no_exp=False),    # no nominal exp_pad
    DfnConfig(2.0, 3.0, 0.5, 8, 0.95, 1.00, 0.40, 1.75, 1.90, 'V2030D-2,VCED-2', no_exp=False),    # no nominal exp_pad
    DfnConfig(2.0, 3.0, 0.5, 8, 0.75, 0.80, 0.40, 1.75, 1.90, 'W2030D-2,WCED-2', no_exp=False),    # no nominal exp_pad
    DfnConfig(2.0, 3.0, 0.5, 8, 0.95, 1.00, 0.45, 1.60, 1.60, 'V2030D-3,VCED-3', no_exp=False),    # no nominal pad length and exp_pad  # noqa: E501
    DfnConfig(2.0, 3.0, 0.5, 8, 0.75, 0.80, 0.45, 1.60, 1.60, 'W2030D-3,WCED-3', no_exp=False),    # no nominal pad length and exp_pad  # noqa: E501
    DfnConfig(2.0, 3.0, 0.5, 8, 0.55, 0.65, 0.45, 1.60, 1.60, 'U2030D', no_exp=False),      # no nominal pad length and exp_pad  # noqa: E501
    # Rectangular, Type 1, 2.5 x 3.0
    DfnConfig(2.5, 3.0, 0.8, 6, 0.95, 1.00, 0.55, 1.50, 1.20, 'V2530B,VDEB'),
    DfnConfig(2.5, 3.0, 0.8, 6, 0.75, 0.80, 0.55, 1.50, 1.20, 'W2530B,WDEB'),
    DfnConfig(2.5, 3.0, 0.5, 8, 0.95, 1.00, 0.55, 1.50, 1.20, 'V2530D,VDED'),
    DfnConfig(2.5, 3.0, 0.5, 8, 0.75, 0.80, 0.55, 1.50, 1.20, 'W2530D,WDED'),
    # Rectangular, Type 1, 3.0 x 4.0
    DfnConfig(3.0, 4.0, 0.8, 6, 0.95, 1.00, 0.55, 2.00, 2.20, 'V3040B,VEGB'),
    DfnConfig(3.0, 4.0, 0.8, 6, 0.75, 0.80, 0.55, 2.00, 2.20, 'W3040B,WEGB'),
    DfnConfig(3.0, 4.0, 0.5, 10, 0.95, 1.00, 0.55, 2.00, 2.20, 'V3040D,VEGD'),
    DfnConfig(3.0, 4.0, 0.5, 10, 0.75, 0.80, 0.55, 2.00, 2.20, 'W3040D,WEGD'),
    # Rectangular, Type 1, 4.0 x 5.0
    DfnConfig(4.0, 5.0, 0.8, 10, 0.95, 1.00, 0.55, 3.00, 3.20, 'V4050B,VGJB'),
    DfnConfig(4.0, 5.0, 0.8, 10, 0.75, 0.80, 0.55, 3.00, 3.20, 'W4050B,WGJB'),
    DfnConfig(4.0, 5.0, 0.5, 14, 0.95, 1.00, 0.55, 3.00, 3.20, 'V4050D,VGJD'),
    DfnConfig(4.0, 5.0, 0.5, 14, 0.75, 0.80, 0.55, 3.00, 3.20, 'W4050D,WGJD'),
    # Table 7
    # Rectangular, Type 2, 1.5 x 1.0
    DfnConfig(1.5, 1.0, 0.5, 4, 0.95, 1.00, 0.30, 0.00, 0.00, 'V1510D,VBAD'),
    DfnConfig(1.5, 1.0, 0.5, 4, 0.75, 0.80, 0.30, 0.00, 0.00, 'W1510D,VBAD'),
    # Rectangular, Type 2, 2.0 x 1.0
    DfnConfig(2.0, 1.0, 0.5, 4, 0.95, 1.00, 0.30, 0.00, 0.00, 'V2010D-1,VCAD-1'),
    DfnConfig(2.0, 1.0, 0.5, 4, 0.75, 0.80, 0.30, 0.00, 0.00, 'W2010D-1,WCAD-1'),
    DfnConfig(2.0, 1.0, 0.5, 6, 0.95, 1.00, 0.30, 0.00, 0.00, 'V2010D-2,VCAD-2'),
    DfnConfig(2.0, 1.0, 0.5, 6, 0.75, 0.80, 0.30, 0.00, 0.00, 'W2010D-2,WCAD-2'),
    # Rectangular, Type 2, 2.0 x 1.5
    DfnConfig(2.0, 1.5, 0.5, 4, 0.95, 1.00, 0.55, 1.20, 0.10, 'V2015D-1,VCBD-1'),
    DfnConfig(2.0, 1.5, 0.5, 4, 0.75, 0.80, 0.55, 1.20, 0.10, 'W2015D-1,WCBD-1'),
    DfnConfig(2.0, 1.5, 0.5, 6, 0.95, 1.00, 0.55, 1.20, 0.10, 'V2015D-2,VCBD-2'),
    DfnConfig(2.0, 1.5, 0.5, 6, 0.75, 0.80, 0.55, 1.20, 0.10, 'W2015D-2,WCBD-2'),
    # Rectangular, Type 2, 2.5 x 1.5
    DfnConfig(2.5, 1.5, 0.5, 6, 0.95, 1.00, 0.55, 1.70, 0.10, 'V2515D-1,VDBD-1'),
    DfnConfig(2.5, 1.5, 0.5, 6, 0.75, 0.80, 0.55, 1.70, 0.10, 'W2515D-1,WDBD-1'),
    DfnConfig(2.5, 1.5, 0.5, 8, 0.95, 1.00, 0.55, 1.70, 0.10, 'V2515D-2,VDBD-2'),
    DfnConfig(2.5, 1.5, 0.5, 8, 0.75, 0.80, 0.55, 1.70, 0.10, 'W2515D-2,WDBD-2'),
    # Rectangular, Type 2, 2.5 x 2.0
    DfnConfig(2.5, 2.0, 0.5, 4, 0.95, 1.00, 0.55, 1.70, 0.60, 'V2520D-1,VDCD-1'),
    DfnConfig(2.5, 2.0, 0.5, 4, 0.75, 0.80, 0.55, 1.70, 0.60, 'W2520D-1,WDCD-1'),
    DfnConfig(2.5, 2.0, 0.5, 6, 0.95, 1.00, 0.55, 1.70, 0.60, 'V2520D-2,VDCD-2'),
    DfnConfig(2.5, 2.0, 0.5, 6, 0.75, 0.80, 0.55, 1.70, 0.60, 'W2520D-2,WDCD-2'),
    DfnConfig(2.5, 2.0, 0.5, 8, 0.95, 1.00, 0.55, 1.70, 0.60, 'V2520D-3,VDCD-3'),
    DfnConfig(2.5, 2.0, 0.5, 8, 0.75, 0.80, 0.55, 1.70, 0.60, 'W2520D-3,WDCD-3'),
    # Rectangular, Type 2, 3.0 x 1.5
    DfnConfig(3.0, 1.5, 0.5, 8, 0.95, 1.00, 0.55, 2.20, 0.10, 'V3015D-1,VEBD-1'),
    DfnConfig(3.0, 1.5, 0.5, 8, 0.75, 0.80, 0.55, 2.20, 0.10, 'W3015D-1,WEBD-1'),
    DfnConfig(3.0, 1.5, 0.5, 10, 0.95, 1.00, 0.55, 2.20, 0.10, 'W3015D-2,VEBD-2'),
    DfnConfig(3.0, 1.5, 0.5, 10, 0.75, 0.80, 0.55, 2.20, 0.10, 'W3015D-2,WEBD-2'),
    # Rectangular, Type 2, 3.0 x 2.0
    DfnConfig(3.0, 2.0, 0.95, 6, 0.95, 1.00, 0.30, 2.20, 0.60, 'V3020A,VECA'),    # no nominal exp_pad, using manual values  # noqa: E501
    DfnConfig(3.0, 2.0, 0.65, 8, 0.95, 1.00, 0.30, 2.20, 0.60, 'V3020C,VECC'),    # no nominal exp_pad, using manual values  # noqa: E501
    DfnConfig(3.0, 2.0, 0.5, 8, 0.95, 1.00, 0.55, 2.20, 0.60, 'V3020D-1,V3020D-4,VECD-1,VECD-4'),
    DfnConfig(3.0, 2.0, 0.5, 8, 0.75, 0.80, 0.55, 2.20, 0.60, 'W3020D-1,W3020D-4,WECD-1,WECD-4'),
    # Commented out as they coincide with the V3020D-1, only the tolerances are different,
    # so we may need to re-add them again later.
    # DfnConfig(3.0, 2.0, 0.5, 8, 0.95, 1.00, 0.40, 2.20, 0.60, 'V3020D-4,VECD-4', no_exp=False), # no nominal exp_pad
    # DfnConfig(3.0, 2.0, 0.5, 8, 0.75, 0.80, 0.40, 2.20, 0.60, 'W3020D-4,WECD-4', no_exp=False), # no nominal exp_pad
    DfnConfig(3.0, 2.0, 0.5, 10, 0.95, 1.00, 0.55, 2.20, 0.60, 'V3020D-2,VECD-2', print_pad=True),
    DfnConfig(3.0, 2.0, 0.5, 10, 0.75, 0.80, 0.55, 2.20, 0.60, 'W3020D-2,WECD-2'),
    DfnConfig(3.0, 2.0, 0.5, 10, 0.95, 1.00, 0.30, 2.20, 0.60, 'V3020D-3,VECD-3', print_pad=True),
    # Rectangular, Type 2, 3.0 x 2.5
    DfnConfig(3.0, 2.5, 0.5, 8, 0.95, 1.00, 0.55, 2.20, 1.10, 'V3025D-1,VEDD-1'),
    DfnConfig(3.0, 2.5, 0.5, 8, 0.75, 0.80, 0.55, 2.20, 1.10, 'V3025D-1,WEDD-1'),
    DfnConfig(3.0, 2.5, 0.5, 10, 0.95, 1.00, 0.50, 2.20, 1.10, 'V3025D-2,VEDD-2'),
    DfnConfig(3.0, 2.5, 0.5, 10, 0.75, 0.80, 0.50, 2.20, 1.10, 'V3025D-2,WEDD-2'),
    # Rectangular, Type 2, 3.5 x 2.5
    DfnConfig(3.5, 2.5, 0.5, 10, 0.95, 1.00, 0.55, 2.70, 1.10, 'V3525D-1,VFDD-1'),
    DfnConfig(3.5, 2.5, 0.5, 10, 0.75, 0.80, 0.55, 2.70, 1.10, 'W3525D-1,WFDD-1'),
    DfnConfig(3.5, 2.5, 0.5, 12, 0.95, 1.00, 0.55, 2.70, 1.10, 'V3525D-2,VFDD-2'),
    DfnConfig(3.5, 2.5, 0.5, 12, 0.75, 0.80, 0.55, 2.70, 1.10, 'W3525D-2,WFDD-2'),
    # Rectangular, Type 2, 3.5 x 3.0
    DfnConfig(3.5, 3.0, 0.5, 10, 0.95, 1.00, 0.55, 2.70, 1.60, 'V3530D-1,VFED-1'),
    DfnConfig(3.5, 3.0, 0.5, 10, 0.75, 0.80, 0.55, 2.70, 1.60, 'W3530D-1,WFED-1'),
    DfnConfig(3.5, 3.0, 0.5, 12, 0.95, 1.00, 0.55, 2.70, 1.60, 'V3530D-2,VFED-2'),
    DfnConfig(3.5, 3.0, 0.5, 12, 0.75, 0.80, 0.55, 2.70, 1.60, 'W3530D-2,WFED-2'),
    # Rectangular, Type 2, 4.0 x 3.0
    DfnConfig(4.0, 3.0, 0.5, 10, 0.95, 1.00, 0.55, 3.20, 1.60, 'V4030D-1,VGED-1'),
    DfnConfig(4.0, 3.0, 0.5, 10, 0.75, 0.80, 0.55, 3.20, 1.60, 'W4030D-1,WGED-1'),
    DfnConfig(4.0, 3.0, 0.5, 12, 0.95, 1.00, 0.55, 3.20, 1.60, 'V4030D-2,VGED-2'),
    DfnConfig(4.0, 3.0, 0.5, 12, 0.75, 0.80, 0.55, 3.20, 1.60, 'W4030D-2,WGED-2'),
    DfnConfig(4.0, 3.0, 0.5, 12, 0.95, 1.00, 0.40, 3.70, 1.80, 'V4030D-4,VGED-4', no_exp=False),    # no nominal exp_pad
    DfnConfig(4.0, 3.0, 0.5, 12, 0.75, 0.80, 0.40, 3.70, 1.80, 'W4030D-4,WGED-4', no_exp=False),    # no nominal exp_pad
    DfnConfig(4.0, 3.0, 0.5, 14, 0.95, 1.00, 0.55, 3.20, 1.60, 'V4030D-3,VGED-3'),
    DfnConfig(4.0, 3.0, 0.5, 14, 0.75, 0.80, 0.55, 3.20, 1.60, 'W4030D-3,WGED-3'),
    # Rectangular, Type 2, 5.0 x 3.0
    DfnConfig(5.0, 3.0, 0.5, 16, 0.95, 1.00, 0.55, 4.20, 1.60, 'V5030D-1,VJED-1'),
    DfnConfig(5.0, 3.0, 0.5, 16, 0.75, 0.80, 0.55, 4.20, 1.60, 'W5030D-1,WJED-1'),
    DfnConfig(5.0, 3.0, 0.5, 18, 0.95, 1.00, 0.55, 4.20, 1.60, 'V5030D-2,VJED-2'),
    DfnConfig(5.0, 3.0, 0.5, 18, 0.75, 0.80, 0.55, 4.20, 1.60, 'W5030D-2,WJED-2'),
    # Rectangular, Type 2, 5.0 x 4.0
    DfnConfig(5.0, 4.0, 0.5, 14, 0.95, 1.00, 0.55, 4.20, 2.60, 'V5040D-1,VJGD-1'),
    DfnConfig(5.0, 4.0, 0.5, 14, 0.75, 0.80, 0.55, 4.20, 2.60, 'W5040D-1,WJGD-1'),
    DfnConfig(5.0, 4.0, 0.5, 16, 0.95, 1.00, 0.55, 4.20, 2.60, 'V5040D-2,VJGD-2'),
    DfnConfig(5.0, 4.0, 0.5, 16, 0.75, 0.80, 0.55, 4.20, 2.60, 'W5040D-2,WJGD-2'),
    DfnConfig(5.0, 4.0, 0.5, 18, 0.95, 1.00, 0.55, 4.20, 2.60, 'V5040D-3,VJGD-3'),
    DfnConfig(5.0, 4.0, 0.5, 18, 0.75, 0.80, 0.55, 4.20, 2.60, 'W5040D-3,WJGD-3'),
    # Rectangular, Type 2, 6.0 x 5.0
    DfnConfig(6.0, 5.0, 0.5, 16, 0.95, 1.00, 0.55, 4.70, 3.40, 'V6050D-1,VLJD-1', no_exp=False),    # no nominal exp_pad
    DfnConfig(6.0, 5.0, 0.5, 16, 0.75, 0.80, 0.55, 4.70, 3.40, 'W6050D-1,WLJD-1', no_exp=False),    # no nominal exp_pad
    DfnConfig(6.0, 5.0, 0.5, 18, 0.95, 1.00, 0.55, 4.70, 3.40, 'V6050D-2,VLJD-2', no_exp=False),    # no nominal exp_pad
    DfnConfig(6.0, 5.0, 0.5, 18, 0.75, 0.80, 0.55, 4.70, 3.40, 'W6050D-2,WLJD-2', no_exp=False),    # no nominal exp_pad
]
# fmt: on


def draw_circle(diameter: float) -> Callable[[DfnConfig, Callable[[str], str], Footprint], None]:
    def _draw(config: DfnConfig, uuid: Callable[[str], str], footprint: Footprint) -> None:
        footprint.add_circle(Circle(
            uuid('hole-circle-doc'),
            Layer('top_documentation'),
            Width(0.1),
            Fill(False),
            GrabArea(False),
            Diameter(diameter),
            Position(0, 0),
        ))
    return _draw


def draw_rect(x: float, y: float, width: float, height: float) -> Callable[[DfnConfig, Callable[[str], str], Footprint], None]:
    def _draw(config: DfnConfig, uuid: Callable[[str], str], footprint: Footprint) -> None:
        footprint.add_polygon(Polygon(
            uuid=uuid('hole-polygon-doc'),
            layer=Layer('top_documentation'),
            width=Width(0),
            fill=Fill(True),
            grab_area=GrabArea(False),
            vertices=[
                Vertex(Position(x - width / 2, y + height / 2), Angle(0)),
                Vertex(Position(x + width / 2, y + height / 2), Angle(0)),
                Vertex(Position(x + width / 2, y - height / 2), Angle(0)),
                Vertex(Position(x - width / 2, y - height / 2), Angle(0)),
                Vertex(Position(x - width / 2, y + height / 2), Angle(0)),
            ],
        ))
    return _draw


def step_modification_sphere(diameter: float) -> StepModificationFn:
    def _fn(body: Any, dot: Any, workplane: Any) -> Tuple[Any, Any]:
        return body.cut(workplane.sphere(diameter / 2, centered=True)), dot
    return _fn


def step_modification_cylinder(x: float, y: float, diameter: float, length: float) -> StepModificationFn:
    def _fn(body: Any, dot: Any, workplane: Any) -> Tuple[Any, Any]:
        cutout = workplane.transformed(offset=(x, y, 0), rotate=(0, 90, 0)) \
            .cylinder(length, diameter / 2, centered=True)
        return body.cut(cutout), dot
    return _fn


def step_modification_sgp3x(body: Any, dot: Any, workplane: Any) -> Tuple[Any, Any]:
    dot = workplane.cylinder(0.2, 0.6, centered=[True, True, False]) \
        .transformed(offset=(0.5, 0.5, 0), rotate=(0, 0, 45)) \
        .box(0.3, 0.3, 0.3, centered=[True, True, False])
    return body, dot


# fmt: off
THIRD_CONFIGS = [
    # Sensirion
    DfnConfig(
        length=2.0,
        width=2.0,
        pitch=1.0,
        pin_count=4,
        height_nominal=0.75,
        height_max=0.80,
        lead_length=0.35,
        lead_width=0.35,
        exposed_width=1.60,
        exposed_length=0.70,
        keywords='sensirion,sht,shtcx,shtc1,shtc3',
        name='SENSIRION_SHTCx',
        create_date='2019-01-24T21:50:44Z',
        library="Sensirion.lplib",
        no_exp=False,
        pin1_corner_dx_dy=0.2,
        extended_doc_fn=draw_circle(diameter=0.9),
        step_modification_fn=step_modification_sphere(0.9),
    ),
    DfnConfig(
        length=3.0,
        width=3.0,
        pitch=1.0,
        pin_count=6,
        height_nominal=1.1,
        height_max=1.20,
        lead_length=0.4,
        lead_width=0.4,
        exposed_width=2.4,
        exposed_length=1.5,
        keywords='sensirion,sht,sht2x,sht20,sht21,sht25',
        name='SENSIRION_SHT2x',
        create_date='2019-01-24T22:13:46Z',
        library="Sensirion.lplib",
        no_exp=False,
        pin1_corner_dx_dy=0.2,
        extended_doc_fn=draw_rect(x=0, y=-0.7, width=2.2, height=0.6),
        step_modification_fn=step_modification_cylinder(x=0, y=-0.7, diameter=0.6, length=2.2),
    ),
    DfnConfig(
        length=2.45,
        width=2.45,
        pitch=0.8,
        pin_count=6,
        height_nominal=0.9,
        height_max=0.9,
        lead_length=0.35,
        lead_width=0.4,
        exposed_width=1.7,
        exposed_length=1.25,
        keywords='sensirion,sgp,sgp30,sgpc3',
        name='SENSIRION_SGP30_SGPC3',  # SGP4x needs different 3D model
        create_date='2019-12-27T19:39:48Z',
        library="Sensirion.lplib",
        no_exp=False,
        pin1_corner_dx_dy=0.3,
        extended_doc_fn=draw_circle(diameter=1.1),
        step_modification_fn=step_modification_sgp3x,
    ),

    # Microchip
    DfnConfig(
        length=2.0,
        width=3.0,
        pitch=0.5,
        pin_count=8,
        height_nominal=0.90,
        height_max=1.00,
        lead_length=0.40,
        exposed_width=1.45,
        exposed_length=1.75,
        keywords='microchip mc',
        create_date='2020-11-01T17:32:01Z',
        no_exp=False,
    ),
]
# fmt: on
