"""
Generate the following SO packages:

- VQFN / WQFN

Relevant standards:

- JEDEC MS-220 https://www.jedec.org/system/files/docs/MO-220K01.pdf

"""
from collections import namedtuple
from copy import deepcopy
from itertools import chain
from os import makedirs, path
from uuid import uuid4

from typing import Iterable, List, Optional

from common import COURTYARD_LINE_WIDTH
from common import format_float as ff
from common import format_ipc_dimension as fd
from common import init_cache, now, save_cache, sign

import math as m

generator = 'librepcb-parts-generator (generate_qfn.py)'

line_width = 0.25
pkg_text_height = 1.0
text_y_offset = 1.0
silkscreen_offset = 0.150  # 150 µm

# Initialize UUID cache
uuid_cache_file = 'uuid_cache_qfn.csv'
uuid_cache = init_cache(uuid_cache_file)

# IPC-7351 Table 3-13;
# If anything in J_H or J_S becomes positive for some reason, the code
# for avoiding too-close pads will need to be changed.
J_T = { 'C': 0.20, 'B': 0.30, 'A': 0.40 };
J_H = { 'C': 0.00, 'B': 0.00, 'A': 0.00 };
J_S = { 'C': -0.04, 'B': -0.04, 'A': -0.04 };
courtyard = { 'C': 0.1, 'B': 0.25, 'A': 0.5 };

class Pad:
    def __init__(self, x: float, y: float, l: float, w: float,
            orientation: str):
        self.x = x
        self.y = y
        self.w = w;
        self.l = l;
        self.orientation = orientation  # Either 'horizontal' or 'vertical'

class QfnCnf:

    def __init__( self,
            variation: str, # E.g. VEEB, WJHB
            A: float, # Height
            e: float, # Pitch
            D: float, E: float, # Body size
            D2: float, E2: float, # EPad size
            L: float, # Pad length
            ND: int, NE: int ): # Pins on each side
        self.variation = variation;
        self.A = A;
        self.e = e;
        self.D = D; self.E = E;
        self.E2 = E2; self.D2 = D2;
        self.L = L;
        self.ND = ND; self.NE = NE;
        self.N = 2 * ND + 2 * NE;
        self.bmax = { # JEDEC MO-220 K.01 Table 3, 'MAX' column
            1.00: 0.45, 0.80: 0.35, 0.65: 0.35, 0.50: 0.30, 0.40: 0.25,
        }[self.e];

        # Make sure that our corner pins aren't too close to each other
        # by reducing L.

        # Distance from corner to where first pad starts
        x = self.D / 2 - \
            ( self.e * ( self.ND - 1 ) / 2 + self.bmax / 2 );
        y = self.E / 2 - \
            ( self.e * ( self.NE - 1 ) / 2 + self.bmax / 2 );

        d = m.sqrt( pow( max( [ x - self.L, 0 ] ), 2 ) + \
            pow( max( [ y - self.L, 0 ] ), 2 ) );

        if d < 0.2:
            # Subtracting a little bit extra to avoid floaing point
            # error at the assert down there difference should dissapear
            # when formatting anyway.
            if x - y >= 0.2:
                self.L = x - 0.2001;
            elif y - x >= 0.2:
                self.L = y - 0.2001;
            else:
                self.L = 0.5 * ( x + y ) - m.sqrt( \
                    x * y / 2 - ( x * x + y * y ) / 4 + 0.02 ) - 0.001;
            d = m.sqrt( pow( max( [ x - self.L, 0 ] ), 2 ) + \
                pow( max( [ y - self.L, 0 ] ), 2 ) );
        assert d >= 0.2, 'Got my length sums wrong. :(';

        # Make sure there's at least 200µm between edge pads and the
        # exposed pad.  Figures out which dimention is worse, shrinks L
        # and D2/E2 accordingly, then handles other dimension if needed.
        if 0.2 > self.D / 2 - ( self.L + self.D2 / 2 ) or \
                0.2 > self.E / 2 - ( self.L + self.E2 / 2 ):

            d_adj = 0.2 - ( self.D / 2 - ( self.L + self.D2 / 2 ) );
            e_adj = 0.2 - ( self.E / 2 - ( self.L + self.E2 / 2 ) );

            if d_adj > e_adj:
                self.D2 -= d_adj;
                self.L -= d_adj / 2;
                if e_adj > d_adj / 2:
                    self.E2 -= 2 * ( e_adj - d_adj / 2);
            else:
                self.E2 -= e_adj;
                self.L -= e_adj / 2;
                if d_adj > e_adj / 2:
                    self.D2 -= 2 * ( d_adj - e_adj / 2);

            # Prevent rounding from eating into our 200µm later on
            self.L -= self.L % 0.01;
            self.E2 -= self.E2 % 0.01;
            self.D2 -= self.D2 % 0.01;

            assert self.L > 0 and self.E2 > 0 and self.D2 > 0, \
                'Not big enough to have 200µm between pads and epad';


    def get_configs(self) -> List['QfnCnf']:
        return[self];

    def ipc_name(self) -> str:
        return '{}QFN{}P{}X{}X{}-{}-{}'.format(
            self.variation[0],
            fd(self.e),
            fd(self.D),
            fd(self.E),
            fd(self.A),
            self.N, self.variation,
        )

    def description(self) -> str:
        if 'V' == self.variation[0]:
            full_name = 'Very Thin Quad Flat No Lead Package (VQFN)'
        elif 'W' == self.variation[0]:
            full_name = \
                'Very Very Thin Quad Flat No Lead Package (WQFN)'
        else:
            raise ValueError(
                'Invalid variation: {}'.format(self.variation))
        return '{}-pin {}, standardized by JEDEC in MO-220. ' \
               'Variation {}\\n\\n' \
               'Pitch: {} mm\\nBody size: {}x{} mm\\n' \
               'Max height: {} mm'.format(
                   self.N, full_name, self.variation, self.e,
                   self.D, self.E, self.A,
               )

    def get_pad_coords( self, pad_number: int, density: str ) -> Pad:
        # side - true for E side, false for D side
        # half - true for top/right, false for bottom/left
        # side_number - number of pin pitches around from the half way
        #    mark
        if pad_number <= self.NE:
            side = True;
            half = False;
            side_number = pad_number - ( self.NE + 1 ) / 2;
        elif pad_number <= self.NE + self.ND:
            side = False;
            half = False;
            side_number = ( pad_number - self.NE ) - \
                ( self.ND + 1 ) / 2;
        elif pad_number <= 2 * self.NE + self.ND:
            side = True;
            half = True;
            side_number = ( pad_number - self.NE - self.ND ) - \
                ( self.NE + 1 ) / 2;
        elif pad_number <= 2 * self.NE + 2 * self.ND:
            side = False;
            half = True;
            side_number = ( pad_number - 2 * self.NE - self.ND ) - \
                (self.ND + 1 ) / 2;
        else:
            assert pad_number <= 2 * self.NE + 2 * self.ND, \
                "Bad pad number";

        # A lazy man's reading of IPC-7351:
        # - Your pads should extend J_T mm past the outline of the
        #   package.
        # - They should extend back in by the maximum length of the pin
        #   plus J_H mm.
        # - Their width should be the maximum width of the pin plus
        #   J_S mm on each side.

        l = self.L + J_T[density] + J_H[density];
        w = self.bmax + 2 * J_S[density];
        if side:
            x = self.D / 2 + J_T[density] - l / 2;
            y = side_number * self.e;
        else:
            y = self.E / 2 + J_T[density] - l / 2;
            x = - side_number * self.e;

        if not half:
            x *= -1;
            y *= -1;

        return Pad( x, y, l, w, 'horizontal' if side else 'vertical' );

    def get_pin_extent( self, density: str ):

        # This function returns the distance from the centre line to
        # the outside edge of the furthest pin.  Used for drawing the
        # silkscreen.

        x = self.e * self.ND / 2 + self.bmax / 2 + J_S[density];
        y = self.e * self.NE / 2 + self.bmax / 2 + J_S[density];

        return x, y;


JEDEC_CONFIGS = [  # May contain any type that has a `get_configs(self) -> List[QfpConfig]` method

    # These numbers are taken from tables 6, 7 & 8 in
    # https://www.jedec.org/system/files/docs/MO-220K01.pdf, rows
    # VARIATION, D, E, D2 MAX, E2 MAX, L MAX, ND, NE.  The value for A
    # is 1 for V* variations, 0.8 for W* variations.  e is given at the
    # top of each table.

    #       Variation  A    e     D    E    D2    E2    L      ND  NE
    QfnCnf( 'VEEB',    1.0, 0.80, 3.0, 3.0, 1.25, 1.25, 0.75,  1,  1, ),
    QfnCnf( 'VGEB',    1.0, 0.80, 4.0, 3.0, 2.25, 1.25, 0.75,  3,  1, ),
    QfnCnf( 'VGGB',    1.0, 0.80, 4.0, 4.0, 2.25, 2.25, 0.75,  3,  3, ),
    QfnCnf( 'VGGB-1',  1.0, 0.80, 4.0, 4.0, 2.30, 2.30, 0.75,  4,  3, ),
    QfnCnf( 'VGHB',    1.0, 0.80, 4.0, 5.0, 2.30, 3.30, 0.75,  2,  3, ),
    QfnCnf( 'VHGB',    1.0, 0.80, 5.0, 4.0, 3.25, 2.25, 0.75,  4,  3, ),
    QfnCnf( 'VHGB-1',  1.0, 0.80, 5.0, 4.0, 3.30, 2.30, 0.75,  5,  3, ),
    QfnCnf( 'VHHB',    1.0, 0.80, 5.0, 5.0, 3.25, 3.25, 0.75,  4,  4, ),
    QfnCnf( 'VHHB-1',  1.0, 0.80, 5.0, 5.0, 3.30, 3.25, 0.75,  6,  4, ),
    QfnCnf( 'VJHB',    1.0, 0.80, 6.0, 5.0, 4.25, 3.25, 0.75,  5,  4, ),
    QfnCnf( 'VJHB-1',  1.0, 0.80, 6.0, 5.0, 4.30, 3.30, 0.75,  6,  4, ),
    QfnCnf( 'VJJB',    1.0, 0.80, 6.0, 6.0, 4.25, 4.25, 0.75,  5,  5, ),
    QfnCnf( 'VJJB-1',  1.0, 0.80, 6.0, 6.0, 4.30, 4.30, 0.75,  7,  5, ),
    QfnCnf( 'VJJB-2',  1.0, 0.80, 6.0, 6.0, 4.30, 4.30, 0.75,  5,  7, ),
    QfnCnf( 'VKKB',    1.0, 0.80, 7.0, 7.0, 5.25, 5.25, 0.75,  7,  7, ),
    QfnCnf( 'VLLB',    1.0, 0.80, 8.0, 8.0, 6.25, 6.25, 0.75,  8,  8, ),
    QfnCnf( 'VLLB-1',  1.0, 0.80, 8.0, 8.0, 6.30, 6.30, 0.75,  8,  6, ),
    QfnCnf( 'VMMB',    1.0, 0.80, 9.0, 9.0, 7.10, 7.10, 0.75,  9,  9, ),
    QfnCnf( 'VEEC',    1.0, 0.65, 3.0, 3.0, 1.25, 1.25, 0.75,  2,  2, ),
    QfnCnf( 'VEEC-1',  1.0, 0.65, 3.0, 3.0, 1.80, 1.80, 0.45,  3,  3, ),
    QfnCnf( 'VEEC-2',  1.0, 0.65, 3.0, 3.0, 1.80, 1.80, 0.45,  2,  2, ),
    QfnCnf( 'VEEC-3',  1.0, 0.65, 3.0, 3.0, 1.80, 1.80, 0.50,  2,  2, ),
    QfnCnf( 'VGEC',    1.0, 0.65, 4.0, 3.0, 2.25, 1.25, 0.75,  4,  2, ),
    QfnCnf( 'VGGC',    1.0, 0.65, 4.0, 4.0, 2.25, 2.25, 0.75,  4,  4, ),
    QfnCnf( 'VGGC-1',  1.0, 0.65, 4.0, 4.0, 2.80, 2.80, 0.45,  3,  3, ),
    QfnCnf( 'VGGC-2',  1.0, 0.65, 4.0, 4.0, 2.80, 2.80, 0.45,  4,  4, ),
    QfnCnf( 'VGGC-3',  1.0, 0.65, 4.0, 4.0, 2.80, 2.80, 0.50,  4,  4, ),
    QfnCnf( 'VGGC-4',  1.0, 0.65, 4.0, 4.0, 2.60, 2.60, 0.65,  4,  4, ),
    QfnCnf( 'VHGC',    1.0, 0.65, 5.0, 4.0, 3.25, 2.25, 0.75,  5,  4, ),
    QfnCnf( 'VHGC-1',  1.0, 0.65, 5.0, 4.0, 3.70, 2.70, 0.50,  5,  4, ),
    QfnCnf( 'VHHC',    1.0, 0.65, 5.0, 5.0, 3.25, 3.25, 0.75,  5,  5, ),
    QfnCnf( 'VHHC-1',  1.0, 0.65, 5.0, 5.0, 3.80, 3.65, 0.45,  6,  6, ),
    QfnCnf( 'VHHC-2',  1.0, 0.65, 5.0, 5.0, 3.80, 3.65, 0.45,  5,  5, ),
    QfnCnf( 'VHJC',    1.0, 0.65, 5.0, 6.0, 3.80, 4.65, 0.45,  5,  6, ),
    QfnCnf( 'VJHC',    1.0, 0.65, 6.0, 5.0, 4.25, 3.25, 0.75,  6,  5, ),
    QfnCnf( 'VJJC',    1.0, 0.65, 6.0, 6.0, 4.25, 4.25, 0.75,  7,  7, ),
    QfnCnf( 'VJJC-1',  1.0, 0.65, 6.0, 6.0, 4.80, 4.80, 0.45,  6,  6, ),
    QfnCnf( 'VJJC-2',  1.0, 0.65, 6.0, 6.0, 4.80, 4.80, 0.45,  8,  8, ),
    QfnCnf( 'VJJC-3',  1.0, 0.65, 6.0, 6.0, 4.80, 4.80, 0.45,  7,  7, ),
    QfnCnf( 'VJJC-4',  1.0, 0.65, 6.0, 6.0, 4.55, 4.55, 0.50,  7,  7, ),
    QfnCnf( 'VKKC',    1.0, 0.65, 7.0, 7.0, 5.25, 5.25, 0.75,  8,  8, ),
    QfnCnf( 'VKKC-1',  1.0, 0.65, 7.0, 7.0, 5.80, 5.80, 0.45,  9,  9, ),
    QfnCnf( 'VKKC-2',  1.0, 0.65, 7.0, 7.0, 5.80, 5.80, 0.45,  8,  8, ),
    QfnCnf( 'VKMC',    1.0, 0.65, 7.0, 9.0, 5.25, 7.25, 0.65,  8, 11, ),
    QfnCnf( 'VLLC',    1.0, 0.65, 8.0, 8.0, 6.25, 6.25, 0.75, 10, 10, ),
    QfnCnf( 'VLLC-1',  1.0, 0.65, 8.0, 8.0, 6.80, 6.80, 0.45,  9,  9, ),
    QfnCnf( 'VLLC-2',  1.0, 0.65, 8.0, 8.0, 6.80, 6.80, 0.45, 11, 11, ),
    QfnCnf( 'VLLC-3',  1.0, 0.65, 8.0, 8.0, 6.80, 6.80, 0.45, 10, 10, ),
    QfnCnf( 'VLLC-4',  1.0, 0.65, 8.0, 8.0, 6.60, 6.60, 0.50, 11, 11, ),
    QfnCnf( 'VMMC',    1.0, 0.65, 9.0, 9.0, 7.80, 7.80, 0.45, 12, 12, ),
    QfnCnf( 'VMMC-1',  1.0, 0.65, 9.0, 9.0, 7.80, 7.80, 0.45, 11, 11, ),
    QfnCnf( 'VMMC-2',  1.0, 0.65, 9.0, 9.0, 6.75, 6.75, 0.50, 11, 11, ),
    QfnCnf( 'VMMC-3',  1.0, 0.65, 9.0, 9.0, 7.50, 7.50, 0.50, 11, 11, ),
    QfnCnf( 'VCCD',    1.0, 0.50, 2.0, 2.0, 0.80, 0.80, 0.50,  2,  2, ),
    QfnCnf( 'VEED-1',  1.0, 0.50, 3.0, 3.0, 1.25, 1.25, 0.75,  3,  3, ),
    QfnCnf( 'VEED-2',  1.0, 0.50, 3.0, 3.0, 1.25, 1.25, 0.50,  4,  4, ),
    QfnCnf( 'VEED-3',  1.0, 0.50, 3.0, 3.0, 1.80, 1.80, 0.45,  3,  3, ),
    QfnCnf( 'VEED-4',  1.0, 0.50, 3.0, 3.0, 1.80, 1.80, 0.45,  4,  4, ),
    QfnCnf( 'VEED-5',  1.0, 0.50, 3.0, 3.0, 1.65, 1.65, 0.50,  3,  3, ),
    QfnCnf( 'VEED-6',  1.0, 0.50, 3.0, 3.0, 1.65, 1.65, 0.50,  4,  4, ),
    QfnCnf( 'VEED-7',  1.0, 0.50, 3.0, 3.0, 1.45, 1.45, 0.55,  4,  4, ),
    QfnCnf( 'VFFD',    1.0, 0.50, 3.5, 3.5, 2.10, 2.10, 0.60,  5,  5, ),
    QfnCnf( 'VFFD-1',  1.0, 0.50, 3.5, 3.5, 1.80, 1.80, 0.75,  5,  5, ),
    QfnCnf( 'VFSD',    1.0, 0.50, 3.5, 4.5, 2.10, 3.10, 0.60,  4,  8, ),
    QfnCnf( 'VFSD-1',  1.0, 0.50, 3.5, 4.5, 1.80, 2.80, 0.75,  4,  8, ),
    QfnCnf( 'VFSD-2',  1.0, 0.50, 3.5, 4.5, 2.10, 3.10, 0.50,  4,  8, ),
    QfnCnf( 'VGED',    1.0, 0.50, 4.0, 3.0, 2.25, 1.25, 0.75,  5,  3, ),
    QfnCnf( 'VGGD-1',  1.0, 0.50, 4.0, 4.0, 2.25, 2.25, 0.75,  5,  5, ),
    QfnCnf( 'VGGD-2',  1.0, 0.50, 4.0, 4.0, 2.25, 2.25, 0.50,  6,  6, ),
    QfnCnf( 'VGGD-3',  1.0, 0.50, 4.0, 4.0, 2.30, 2.30, 0.75,  4,  3, ),
    QfnCnf( 'VGGD-4',  1.0, 0.50, 4.0, 4.0, 2.30, 2.30, 0.75,  4,  4, ),
    QfnCnf( 'VGGD-5',  1.0, 0.50, 4.0, 4.0, 2.80, 2.80, 0.45,  5,  5, ),
    QfnCnf( 'VGGD-6',  1.0, 0.50, 4.0, 4.0, 2.80, 2.80, 0.45,  6,  6, ),
    QfnCnf( 'VGGD-7',  1.0, 0.50, 4.0, 4.0, 2.90, 2.90, 0.45,  6,  8, ),
    QfnCnf( 'VGGD-8',  1.0, 0.50, 4.0, 4.0, 2.60, 2.60, 0.50,  6,  6, ),
    QfnCnf( 'VGGD-9',  1.0, 0.50, 4.0, 4.0, 2.45, 2.45, 0.55,  6,  6, ),
    QfnCnf( 'VGGD-10', 1.0, 0.50, 4.0, 4.0, 2.60, 2.60, 0.50,  4,  4, ),
    QfnCnf( 'VGGD-11', 1.0, 0.50, 4.0, 4.0, 2.60, 2.60, 0.50,  5,  5, ),
    QfnCnf( 'VGHD',    1.0, 0.50, 4.0, 5.0, 2.25, 3.25, 0.50,  6,  8, ),
    QfnCnf( 'VGHD-1',  1.0, 0.50, 4.0, 5.0, 2.80, 3.80, 0.45,  5,  7, ),
    QfnCnf( 'VGHD-2',  1.0, 0.50, 4.0, 5.0, 2.90, 3.90, 0.45,  6,  6, ),
    QfnCnf( 'VGHD-3',  1.0, 0.50, 4.0, 5.0, 2.80, 3.80, 0.45,  6,  8, ),
    QfnCnf( 'VSTD',    1.0, 0.50, 4.5, 5.5, 3.10, 4.10, 0.60,  6, 10, ),
    QfnCnf( 'VSTD-1',  1.0, 0.50, 4.5, 5.5, 2.80, 3.80, 0.75,  6, 10, ),
    QfnCnf( 'VSUD',    1.0, 0.50, 4.5, 6.5, 3.10, 5.10, 0.60,  6, 12, ),
    QfnCnf( 'VSUD-1',  1.0, 0.50, 4.5, 6.5, 2.80, 4.80, 0.75,  6, 12, ),
    QfnCnf( 'VHGD',    1.0, 0.50, 5.0, 4.0, 3.25, 2.25, 0.75,  7,  5, ),
    QfnCnf( 'VHHD-1',  1.0, 0.50, 5.0, 5.0, 3.35, 3.35, 0.75,  7,  7, ),
    QfnCnf( 'VHHD-2',  1.0, 0.50, 5.0, 5.0, 2.35, 2.35, 0.50,  8,  8, ),
    QfnCnf( 'VHHD-3',  1.0, 0.50, 5.0, 5.0, 3.80, 3.80, 0.45,  7,  7, ),
    QfnCnf( 'VHHD-4',  1.0, 0.50, 5.0, 5.0, 3.80, 3.80, 0.45,  8,  8, ),
    QfnCnf( 'VHHD-5',  1.0, 0.50, 5.0, 5.0, 3.70, 3.70, 0.50,  8,  8, ),
    QfnCnf( 'VHHD-6',  1.0, 0.50, 5.0, 5.0, 3.45, 3.45, 0.55,  8,  8, ),
    QfnCnf( 'VHJD',    1.0, 0.50, 5.0, 6.0, 3.60, 4.60, 0.75,  7,  9, ),
    QfnCnf( 'VHKD',    1.0, 0.50, 5.0, 7.0, 3.25, 5.25, 0.50,  7, 12, ),
    QfnCnf( 'VHKD-1',  1.0, 0.50, 5.0, 7.0, 3.80, 5.80, 0.45,  7, 12, ),
    QfnCnf( 'VHKD-2',  1.0, 0.50, 5.0, 7.0, 3.50, 5.50, 0.50,  8, 12, ),
    QfnCnf( 'VTUD',    1.0, 0.50, 5.5, 6.5, 4.10, 5.10, 0.60,  8, 12, ),
    QfnCnf( 'VTUD-1',  1.0, 0.50, 5.5, 6.5, 3.80, 4.80, 0.65,  8, 12, ),
    QfnCnf( 'VJHD',    1.0, 0.50, 6.0, 5.0, 4.25, 3.25, 0.65,  9,  7, ),
    QfnCnf( 'VJJD-1',  1.0, 0.50, 6.0, 6.0, 4.25, 4.25, 0.75,  9,  9, ),
    QfnCnf( 'VJJD-2',  1.0, 0.50, 6.0, 6.0, 4.25, 4.25, 0.50, 10, 10, ),
    QfnCnf( 'VJJD-3',  1.0, 0.50, 6.0, 6.0, 4.30, 4.30, 0.75, 10,  9, ),
    QfnCnf( 'VJJD-4',  1.0, 0.50, 6.0, 6.0, 4.80, 4.80, 0.45,  9,  9, ),
    QfnCnf( 'VJJD-5',  1.0, 0.50, 6.0, 6.0, 4.80, 4.80, 0.45, 10, 10, ),
    QfnCnf( 'VJJD-6',  1.0, 0.50, 6.0, 6.0, 4.45, 4.45, 0.55, 10, 10, ),
    QfnCnf( 'VJJD-7',  1.0, 0.50, 6.0, 6.0, 4.30, 4.30, 0.75,  8,  8, ),
    QfnCnf( 'VJJD-8',  1.0, 0.50, 6.0, 6.0, 4.60, 4.60, 0.50,  9,  9, ),
    QfnCnf( 'VKHD',    1.0, 0.50, 7.0, 5.0, 5.25, 3.25, 0.50, 12,  7, ),
    QfnCnf( 'VKKD',    1.0, 0.50, 7.0, 7.0, 5.80, 5.80, 0.45, 10, 10, ),
    QfnCnf( 'VKKD-1',  1.0, 0.50, 7.0, 7.0, 5.25, 5.25, 0.75, 11, 11, ),
    QfnCnf( 'VKKD-2',  1.0, 0.50, 7.0, 7.0, 5.25, 5.25, 0.50, 12, 12, ),
    QfnCnf( 'VKKD-3',  1.0, 0.50, 7.0, 7.0, 5.80, 5.80, 0.45, 11, 11, ),
    QfnCnf( 'VKKD-4',  1.0, 0.50, 7.0, 7.0, 5.80, 5.80, 0.45, 12, 12, ),
    QfnCnf( 'VKKD-5',  1.0, 0.50, 7.0, 7.0, 5.30, 5.30, 0.75, 12, 10, ),
    QfnCnf( 'VKKD-6',  1.0, 0.50, 7.0, 7.0, 5.45, 5.45, 0.55, 12, 12, ),
    QfnCnf( 'VKKD-7',  1.0, 0.50, 7.0, 7.0, 5.30, 5.30, 0.75, 10, 12, ),
    QfnCnf( 'VKKD-8',  1.0, 0.50, 7.0, 7.0, 5.20, 5.20, 0.75, 11, 13, ),
    QfnCnf( 'VLLD',    1.0, 0.50, 8.0, 8.0, 6.80, 6.80, 0.45, 12, 12, ),
    QfnCnf( 'VLLD-1',  1.0, 0.50, 8.0, 8.0, 6.25, 6.25, 0.75, 13, 13, ),
    QfnCnf( 'VLLD-2',  1.0, 0.50, 8.0, 8.0, 6.25, 6.25, 0.50, 14, 14, ),
    QfnCnf( 'VLLD-3',  1.0, 0.50, 8.0, 8.0, 6.30, 6.30, 0.75, 13, 11, ),
    QfnCnf( 'VLLD-4',  1.0, 0.50, 8.0, 8.0, 6.80, 6.80, 0.45, 13, 13, ),
    QfnCnf( 'VLLD-5',  1.0, 0.50, 8.0, 8.0, 6.80, 6.80, 0.45, 14, 14, ),
    QfnCnf( 'VLLD-6',  1.0, 0.50, 8.0, 8.0, 6.45, 6.45, 0.55, 14, 14, ),
    QfnCnf( 'VMMD',    1.0, 0.50, 9.0, 9.0, 7.80, 7.80, 0.45, 16, 16, ),
    QfnCnf( 'VMMD-1',  1.0, 0.50, 9.0, 9.0, 7.80, 7.80, 0.45, 15, 15, ),
    QfnCnf( 'VMMD-2',  1.0, 0.50, 9.0, 9.0, 7.80, 7.80, 0.45, 14, 14, ),
    QfnCnf( 'VMMD-3',  1.0, 0.50, 9.0, 9.0, 7.45, 7.45, 0.55, 16, 16, ),
    QfnCnf( 'VMMD-4',  1.0, 0.50, 9.0, 9.0, 7.50, 7.50, 0.50, 16, 16, ),
    QfnCnf( 'VNND-1',  1.0, 0.50, 10., 10., 8.25, 8.25, 0.65, 16, 16, ),
    QfnCnf( 'VNND-2',  1.0, 0.50, 10., 10., 8.25, 8.25, 0.65, 17, 17, ),
    QfnCnf( 'VNND-3',  1.0, 0.50, 10., 10., 8.45, 8.45, 0.55, 18, 18, ),
    QfnCnf( 'VNND-4',  1.0, 0.50, 10., 10., 6.50, 6.50, 0.50, 18, 18, ),
    QfnCnf( 'VRRD',    1.0, 0.50, 12., 12.,10.25,10.25, 0.60, 20, 20, ),
    QfnCnf( 'VEEE',    1.0, 0.40, 3.0, 3.0, 1.25, 1.25, 0.50,  5,  5, ),
    QfnCnf( 'VEEE-1',  1.0, 0.40, 3.0, 3.0, 1.25, 1.25, 0.50,  4,  4, ),
    QfnCnf( 'VGGE',    1.0, 0.40, 4.0, 4.0, 2.25, 2.25, 0.50,  7,  7, ),
    QfnCnf( 'VHHE',    1.0, 0.40, 5.0, 5.0, 3.25, 3.25, 0.50,  9,  9, ),
    QfnCnf( 'VHHE-1',  1.0, 0.40, 5.0, 5.0, 3.75, 3.75, 0.50, 10, 10, ),
    QfnCnf( 'VJJE',    1.0, 0.40, 6.0, 6.0, 4.25, 4.25, 0.50, 12, 12, ),
    QfnCnf( 'VJJE-1',  1.0, 0.40, 6.0, 6.0, 4.75, 4.75, 0.50, 12, 12, ),
    QfnCnf( 'VGHE',    1.0, 0.40, 4.0, 5.0, 2.70, 3.70, 0.50,  7,  9, ),
    QfnCnf( 'VGHE-1',  1.0, 0.40, 4.0, 5.0, 2.70, 3.70, 0.50,  7, 10, ),
    QfnCnf( 'VLLE-1',  1.0, 0.40, 8.0, 8.0, 6.25, 6.25, 0.50, 17, 17, ),
    QfnCnf( 'VLLE-2',  1.0, 0.40, 8.0, 8.0, 6.60, 6.60, 0.50, 16, 16, ),
    QfnCnf( 'VMME',    1.0, 0.40, 9.0, 9.0, 7.25, 7.25, 0.50, 18, 18, ),
    QfnCnf( 'VMME-1',  1.0, 0.40, 9.0, 9.0, 7.25, 7.25, 0.50, 19, 19, ),
    QfnCnf( 'VNNE',    1.0, 0.40, 10., 10., 8.25, 8.25, 0.50, 22, 22, ),
    QfnCnf( 'VNNE-1',  1.0, 0.40, 10., 10., 6.90, 6.90, 0.50, 22, 22, ),
    QfnCnf( 'VKKE',    1.0, 0.40, 7.0, 7.0, 5.25, 5.25, 0.50, 14, 14, ),
    QfnCnf( 'VLLE',    1.0, 0.40, 8.0, 8.0, 6.25, 6.25, 0.50, 16, 16, ),
    QfnCnf( 'VRRE',    1.0, 0.40, 12., 12.,10.25,10.25, 0.50, 25, 25, ),
    QfnCnf( 'VRRE-1',  1.0, 0.40, 12., 12., 6.90, 6.90, 0.50, 25, 25, ),
    QfnCnf( 'VRRE-2',  1.0, 0.40, 12., 12.,10.25,10.25, 0.50, 27, 27, ),

    QfnCnf( 'WEEB',    0.8, 0.80, 3.0, 3.0, 1.25, 1.25, 0.75,  1,  1, ),
    QfnCnf( 'WGEB',    0.8, 0.80, 4.0, 3.0, 2.25, 1.25, 0.75,  3,  1, ),
    QfnCnf( 'WGGB',    0.8, 0.80, 4.0, 4.0, 2.25, 2.25, 0.75,  3,  3, ),
    QfnCnf( 'WGGB-1',  0.8, 0.80, 4.0, 4.0, 2.30, 2.30, 0.75,  4,  3, ),
    QfnCnf( 'WGHB',    0.8, 0.80, 4.0, 5.0, 2.30, 3.30, 0.75,  2,  3, ),
    QfnCnf( 'WHGB',    0.8, 0.80, 5.0, 4.0, 3.25, 2.25, 0.75,  4,  3, ),
    QfnCnf( 'WHGB-1',  0.8, 0.80, 5.0, 4.0, 3.30, 2.30, 0.75,  5,  3, ),
    QfnCnf( 'WHHB',    0.8, 0.80, 5.0, 5.0, 3.25, 3.25, 0.75,  4,  4, ),
    QfnCnf( 'WHHB-1',  0.8, 0.80, 5.0, 5.0, 3.30, 3.25, 0.75,  6,  4, ),
    QfnCnf( 'WJHB',    0.8, 0.80, 6.0, 5.0, 4.25, 3.25, 0.75,  5,  4, ),
    QfnCnf( 'WJHB-1',  0.8, 0.80, 6.0, 5.0, 4.30, 3.30, 0.75,  6,  4, ),
    QfnCnf( 'WJJB',    0.8, 0.80, 6.0, 6.0, 4.25, 4.25, 0.75,  5,  5, ),
    QfnCnf( 'WJJB-1',  0.8, 0.80, 6.0, 6.0, 4.30, 4.30, 0.75,  7,  5, ),
    QfnCnf( 'WJJB-2',  0.8, 0.80, 6.0, 6.0, 4.30, 4.30, 0.75,  5,  7, ),
    QfnCnf( 'WKKB',    0.8, 0.80, 7.0, 7.0, 5.25, 5.25, 0.75,  7,  7, ),
    QfnCnf( 'WLLB',    0.8, 0.80, 8.0, 8.0, 6.25, 6.25, 0.75,  8,  8, ),
    QfnCnf( 'WLLB-1',  0.8, 0.80, 8.0, 8.0, 6.30, 6.30, 0.75,  8,  6, ),
    QfnCnf( 'WMMB',    0.8, 0.80, 9.0, 9.0, 7.10, 7.10, 0.75,  9,  9, ),
    QfnCnf( 'WEEC',    0.8, 0.65, 3.0, 3.0, 1.25, 1.25, 0.75,  2,  2, ),
    QfnCnf( 'WEEC-1',  0.8, 0.65, 3.0, 3.0, 1.80, 1.80, 0.45,  3,  3, ),
    QfnCnf( 'WEEC-2',  0.8, 0.65, 3.0, 3.0, 1.80, 1.80, 0.45,  2,  2, ),
    QfnCnf( 'WEEC-3',  0.8, 0.65, 3.0, 3.0, 1.80, 1.80, 0.50,  2,  2, ),
    QfnCnf( 'WGEC',    0.8, 0.65, 4.0, 3.0, 2.25, 1.25, 0.75,  4,  2, ),
    QfnCnf( 'WGGC',    0.8, 0.65, 4.0, 4.0, 2.25, 2.25, 0.75,  4,  4, ),
    QfnCnf( 'WGGC-1',  0.8, 0.65, 4.0, 4.0, 2.80, 2.80, 0.45,  3,  3, ),
    QfnCnf( 'WGGC-2',  0.8, 0.65, 4.0, 4.0, 2.80, 2.80, 0.45,  4,  4, ),
    QfnCnf( 'WGGC-3',  0.8, 0.65, 4.0, 4.0, 2.80, 2.80, 0.50,  4,  4, ),
    QfnCnf( 'WGGC-4',  0.8, 0.65, 4.0, 4.0, 2.60, 2.60, 0.65,  4,  4, ),
    QfnCnf( 'WHGC',    0.8, 0.65, 5.0, 4.0, 3.25, 2.25, 0.75,  5,  4, ),
    QfnCnf( 'WHGC-1',  0.8, 0.65, 5.0, 4.0, 3.70, 2.70, 0.50,  5,  4, ),
    QfnCnf( 'WHHC',    0.8, 0.65, 5.0, 5.0, 3.25, 3.25, 0.75,  5,  5, ),
    QfnCnf( 'WHHC-1',  0.8, 0.65, 5.0, 5.0, 3.80, 3.65, 0.45,  6,  6, ),
    QfnCnf( 'WHHC-2',  0.8, 0.65, 5.0, 5.0, 3.80, 3.65, 0.45,  5,  5, ),
    QfnCnf( 'WHJC',    0.8, 0.65, 5.0, 6.0, 3.80, 4.65, 0.45,  5,  6, ),
    QfnCnf( 'WJHC',    0.8, 0.65, 6.0, 5.0, 4.25, 3.25, 0.75,  6,  5, ),
    QfnCnf( 'WJJC',    0.8, 0.65, 6.0, 6.0, 4.25, 4.25, 0.75,  7,  7, ),
    QfnCnf( 'WJJC-1',  0.8, 0.65, 6.0, 6.0, 4.80, 4.80, 0.45,  6,  6, ),
    QfnCnf( 'WJJC-2',  0.8, 0.65, 6.0, 6.0, 4.80, 4.80, 0.45,  8,  8, ),
    QfnCnf( 'WJJC-3',  0.8, 0.65, 6.0, 6.0, 4.80, 4.80, 0.45,  7,  7, ),
    QfnCnf( 'WJJC-4',  0.8, 0.65, 6.0, 6.0, 4.55, 4.55, 0.50,  7,  7, ),
    QfnCnf( 'WKKC',    0.8, 0.65, 7.0, 7.0, 5.25, 5.25, 0.75,  8,  8, ),
    QfnCnf( 'WKKC-1',  0.8, 0.65, 7.0, 7.0, 5.80, 5.80, 0.45,  9,  9, ),
    QfnCnf( 'WKKC-2',  0.8, 0.65, 7.0, 7.0, 5.80, 5.80, 0.45,  8,  8, ),
    QfnCnf( 'WKMC',    0.8, 0.65, 7.0, 9.0, 5.25, 7.25, 0.65,  8, 11, ),
    QfnCnf( 'WLLC',    0.8, 0.65, 8.0, 8.0, 6.25, 6.25, 0.75, 10, 10, ),
    QfnCnf( 'WLLC-1',  0.8, 0.65, 8.0, 8.0, 6.80, 6.80, 0.45,  9,  9, ),
    QfnCnf( 'WLLC-2',  0.8, 0.65, 8.0, 8.0, 6.80, 6.80, 0.45, 11, 11, ),
    QfnCnf( 'WLLC-3',  0.8, 0.65, 8.0, 8.0, 6.80, 6.80, 0.45, 10, 10, ),
    QfnCnf( 'WLLC-4',  0.8, 0.65, 8.0, 8.0, 6.60, 6.60, 0.50, 11, 11, ),
    QfnCnf( 'WMMC',    0.8, 0.65, 9.0, 9.0, 7.80, 7.80, 0.45, 12, 12, ),
    QfnCnf( 'WMMC-1',  0.8, 0.65, 9.0, 9.0, 7.80, 7.80, 0.45, 11, 11, ),
    QfnCnf( 'WMMC-2',  0.8, 0.65, 9.0, 9.0, 6.75, 6.75, 0.50, 11, 11, ),
    QfnCnf( 'WMMC-3',  0.8, 0.65, 9.0, 9.0, 7.50, 7.50, 0.50, 11, 11, ),
    QfnCnf( 'WCCD',    0.8, 0.50, 2.0, 2.0, 0.80, 0.80, 0.50,  2,  2, ),
    QfnCnf( 'WEED-1',  0.8, 0.50, 3.0, 3.0, 1.25, 1.25, 0.75,  3,  3, ),
    QfnCnf( 'WEED-2',  0.8, 0.50, 3.0, 3.0, 1.25, 1.25, 0.50,  4,  4, ),
    QfnCnf( 'WEED-3',  0.8, 0.50, 3.0, 3.0, 1.80, 1.80, 0.45,  3,  3, ),
    QfnCnf( 'WEED-4',  0.8, 0.50, 3.0, 3.0, 1.80, 1.80, 0.45,  4,  4, ),
    QfnCnf( 'WEED-5',  0.8, 0.50, 3.0, 3.0, 1.65, 1.65, 0.50,  3,  3, ),
    QfnCnf( 'WEED-6',  0.8, 0.50, 3.0, 3.0, 1.65, 1.65, 0.50,  4,  4, ),
    QfnCnf( 'WEED-7',  0.8, 0.50, 3.0, 3.0, 1.45, 1.45, 0.55,  4,  4, ),
    QfnCnf( 'WFFD',    0.8, 0.50, 3.5, 3.5, 2.10, 2.10, 0.60,  5,  5, ),
    QfnCnf( 'WFFD-1',  0.8, 0.50, 3.5, 3.5, 1.80, 1.80, 0.75,  5,  5, ),
    QfnCnf( 'WFSD',    0.8, 0.50, 3.5, 4.5, 2.10, 3.10, 0.60,  4,  8, ),
    QfnCnf( 'WFSD-1',  0.8, 0.50, 3.5, 4.5, 1.80, 2.80, 0.75,  4,  8, ),
    QfnCnf( 'WFSD-2',  0.8, 0.50, 3.5, 4.5, 2.10, 3.10, 0.50,  4,  8, ),
    QfnCnf( 'WGED',    0.8, 0.50, 4.0, 3.0, 2.25, 1.25, 0.75,  5,  3, ),
    QfnCnf( 'WGGD-1',  0.8, 0.50, 4.0, 4.0, 2.25, 2.25, 0.75,  5,  5, ),
    QfnCnf( 'WGGD-2',  0.8, 0.50, 4.0, 4.0, 2.25, 2.25, 0.50,  6,  6, ),
    QfnCnf( 'WGGD-3',  0.8, 0.50, 4.0, 4.0, 2.30, 2.30, 0.75,  4,  3, ),
    QfnCnf( 'WGGD-4',  0.8, 0.50, 4.0, 4.0, 2.30, 2.30, 0.75,  4,  4, ),
    QfnCnf( 'WGGD-5',  0.8, 0.50, 4.0, 4.0, 2.80, 2.80, 0.45,  5,  5, ),
    QfnCnf( 'WGGD-6',  0.8, 0.50, 4.0, 4.0, 2.80, 2.80, 0.45,  6,  6, ),
    QfnCnf( 'WGGD-7',  0.8, 0.50, 4.0, 4.0, 2.90, 2.90, 0.45,  6,  8, ),
    QfnCnf( 'WGGD-8',  0.8, 0.50, 4.0, 4.0, 2.60, 2.60, 0.50,  6,  6, ),
    QfnCnf( 'WGGD-9',  0.8, 0.50, 4.0, 4.0, 2.45, 2.45, 0.55,  6,  6, ),
    QfnCnf( 'WGGD-10', 0.8, 0.50, 4.0, 4.0, 2.60, 2.60, 0.50,  4,  4, ),
    QfnCnf( 'WGGD-11', 0.8, 0.50, 4.0, 4.0, 2.60, 2.60, 0.50,  5,  5, ),
    QfnCnf( 'WGHD',    0.8, 0.50, 4.0, 5.0, 2.25, 3.25, 0.50,  6,  8, ),
    QfnCnf( 'WGHD-1',  0.8, 0.50, 4.0, 5.0, 2.80, 3.80, 0.45,  5,  7, ),
    QfnCnf( 'WGHD-2',  0.8, 0.50, 4.0, 5.0, 2.90, 3.90, 0.45,  6,  6, ),
    QfnCnf( 'WGHD-3',  0.8, 0.50, 4.0, 5.0, 2.80, 3.80, 0.45,  6,  8, ),
    QfnCnf( 'WSTD',    0.8, 0.50, 4.5, 5.5, 3.10, 4.10, 0.60,  6, 10, ),
    QfnCnf( 'WSTD-1',  0.8, 0.50, 4.5, 5.5, 2.80, 3.80, 0.75,  6, 10, ),
    QfnCnf( 'WSUD',    0.8, 0.50, 4.5, 6.5, 3.10, 5.10, 0.60,  6, 12, ),
    QfnCnf( 'WSUD-1',  0.8, 0.50, 4.5, 6.5, 2.80, 4.80, 0.75,  6, 12, ),
    QfnCnf( 'WHGD',    0.8, 0.50, 5.0, 4.0, 3.25, 2.25, 0.75,  7,  5, ),
    QfnCnf( 'WHHD-1',  0.8, 0.50, 5.0, 5.0, 3.35, 3.35, 0.75,  7,  7, ),
    QfnCnf( 'WHHD-2',  0.8, 0.50, 5.0, 5.0, 2.35, 2.35, 0.50,  8,  8, ),
    QfnCnf( 'WHHD-3',  0.8, 0.50, 5.0, 5.0, 3.80, 3.80, 0.45,  7,  7, ),
    QfnCnf( 'WHHD-4',  0.8, 0.50, 5.0, 5.0, 3.80, 3.80, 0.45,  8,  8, ),
    QfnCnf( 'WHHD-5',  0.8, 0.50, 5.0, 5.0, 3.70, 3.70, 0.50,  8,  8, ),
    QfnCnf( 'WHHD-6',  0.8, 0.50, 5.0, 5.0, 3.45, 3.45, 0.55,  8,  8, ),
    QfnCnf( 'WHJD',    0.8, 0.50, 5.0, 6.0, 3.60, 4.60, 0.75,  7,  9, ),
    QfnCnf( 'WHKD',    0.8, 0.50, 5.0, 7.0, 3.25, 5.25, 0.50,  7, 12, ),
    QfnCnf( 'WHKD-1',  0.8, 0.50, 5.0, 7.0, 3.80, 5.80, 0.45,  7, 12, ),
    QfnCnf( 'WHKD-2',  0.8, 0.50, 5.0, 7.0, 3.50, 5.50, 0.50,  8, 12, ),
    QfnCnf( 'WTUD',    0.8, 0.50, 5.5, 6.5, 4.10, 5.10, 0.60,  8, 12, ),
    QfnCnf( 'WTUD-1',  0.8, 0.50, 5.5, 6.5, 3.80, 4.80, 0.65,  8, 12, ),
    QfnCnf( 'WJHD',    0.8, 0.50, 6.0, 5.0, 4.25, 3.25, 0.65,  9,  7, ),
    QfnCnf( 'WJJD-1',  0.8, 0.50, 6.0, 6.0, 4.25, 4.25, 0.75,  9,  9, ),
    QfnCnf( 'WJJD-2',  0.8, 0.50, 6.0, 6.0, 4.25, 4.25, 0.50, 10, 10, ),
    QfnCnf( 'WJJD-3',  0.8, 0.50, 6.0, 6.0, 4.30, 4.30, 0.75, 10,  9, ),
    QfnCnf( 'WJJD-4',  0.8, 0.50, 6.0, 6.0, 4.80, 4.80, 0.45,  9,  9, ),
    QfnCnf( 'WJJD-5',  0.8, 0.50, 6.0, 6.0, 4.80, 4.80, 0.45, 10, 10, ),
    QfnCnf( 'WJJD-6',  0.8, 0.50, 6.0, 6.0, 4.45, 4.45, 0.55, 10, 10, ),
    QfnCnf( 'WJJD-7',  0.8, 0.50, 6.0, 6.0, 4.30, 4.30, 0.75,  8,  8, ),
    QfnCnf( 'WJJD-8',  0.8, 0.50, 6.0, 6.0, 4.60, 4.60, 0.50,  9,  9, ),
    QfnCnf( 'WKHD',    0.8, 0.50, 7.0, 5.0, 5.25, 3.25, 0.50, 12,  7, ),
    QfnCnf( 'WKKD',    0.8, 0.50, 7.0, 7.0, 5.80, 5.80, 0.45, 10, 10, ),
    QfnCnf( 'WKKD-1',  0.8, 0.50, 7.0, 7.0, 5.25, 5.25, 0.75, 11, 11, ),
    QfnCnf( 'WKKD-2',  0.8, 0.50, 7.0, 7.0, 5.25, 5.25, 0.50, 12, 12, ),
    QfnCnf( 'WKKD-3',  0.8, 0.50, 7.0, 7.0, 5.80, 5.80, 0.45, 11, 11, ),
    QfnCnf( 'WKKD-4',  0.8, 0.50, 7.0, 7.0, 5.80, 5.80, 0.45, 12, 12, ),
    QfnCnf( 'WKKD-5',  0.8, 0.50, 7.0, 7.0, 5.30, 5.30, 0.75, 12, 10, ),
    QfnCnf( 'WKKD-6',  0.8, 0.50, 7.0, 7.0, 5.45, 5.45, 0.55, 12, 12, ),
    QfnCnf( 'WKKD-7',  0.8, 0.50, 7.0, 7.0, 5.30, 5.30, 0.75, 10, 12, ),
    QfnCnf( 'WKKD-8',  0.8, 0.50, 7.0, 7.0, 5.20, 5.20, 0.75, 11, 13, ),
    QfnCnf( 'WLLD',    0.8, 0.50, 8.0, 8.0, 6.80, 6.80, 0.45, 12, 12, ),
    QfnCnf( 'WLLD-1',  0.8, 0.50, 8.0, 8.0, 6.25, 6.25, 0.75, 13, 13, ),
    QfnCnf( 'WLLD-2',  0.8, 0.50, 8.0, 8.0, 6.25, 6.25, 0.50, 14, 14, ),
    QfnCnf( 'WLLD-3',  0.8, 0.50, 8.0, 8.0, 6.30, 6.30, 0.75, 13, 11, ),
    QfnCnf( 'WLLD-4',  0.8, 0.50, 8.0, 8.0, 6.80, 6.80, 0.45, 13, 13, ),
    QfnCnf( 'WLLD-5',  0.8, 0.50, 8.0, 8.0, 6.80, 6.80, 0.45, 14, 14, ),
    QfnCnf( 'WLLD-6',  0.8, 0.50, 8.0, 8.0, 6.45, 6.45, 0.55, 14, 14, ),
    QfnCnf( 'WMMD',    0.8, 0.50, 9.0, 9.0, 7.80, 7.80, 0.45, 16, 16, ),
    QfnCnf( 'WMMD-1',  0.8, 0.50, 9.0, 9.0, 7.80, 7.80, 0.45, 15, 15, ),
    QfnCnf( 'WMMD-2',  0.8, 0.50, 9.0, 9.0, 7.80, 7.80, 0.45, 14, 14, ),
    QfnCnf( 'WMMD-3',  0.8, 0.50, 9.0, 9.0, 7.45, 7.45, 0.55, 16, 16, ),
    QfnCnf( 'WMMD-4',  0.8, 0.50, 9.0, 9.0, 7.50, 7.50, 0.50, 16, 16, ),
    QfnCnf( 'WNND-1',  0.8, 0.50, 10., 10., 8.25, 8.25, 0.65, 16, 16, ),
    QfnCnf( 'WNND-2',  0.8, 0.50, 10., 10., 8.25, 8.25, 0.65, 17, 17, ),
    QfnCnf( 'WNND-3',  0.8, 0.50, 10., 10., 8.45, 8.45, 0.55, 18, 18, ),
    QfnCnf( 'WNND-4',  0.8, 0.50, 10., 10., 6.50, 6.50, 0.50, 18, 18, ),
    QfnCnf( 'WRRD',    0.8, 0.50, 12., 12.,10.25,10.25, 0.60, 20, 20, ),
    QfnCnf( 'WEEE',    0.8, 0.40, 3.0, 3.0, 1.25, 1.25, 0.50,  5,  5, ),
    QfnCnf( 'WEEE-1',  0.8, 0.40, 3.0, 3.0, 1.25, 1.25, 0.50,  4,  4, ),
    QfnCnf( 'WGGE',    0.8, 0.40, 4.0, 4.0, 2.25, 2.25, 0.50,  7,  7, ),
    QfnCnf( 'WHHE',    0.8, 0.40, 5.0, 5.0, 3.25, 3.25, 0.50,  9,  9, ),
    QfnCnf( 'WHHE-1',  0.8, 0.40, 5.0, 5.0, 3.75, 3.75, 0.50, 10, 10, ),
    QfnCnf( 'WJJE',    0.8, 0.40, 6.0, 6.0, 4.25, 4.25, 0.50, 12, 12, ),
    QfnCnf( 'WJJE-1',  0.8, 0.40, 6.0, 6.0, 4.75, 4.75, 0.50, 12, 12, ),
    QfnCnf( 'WGHE',    0.8, 0.40, 4.0, 5.0, 2.70, 3.70, 0.50,  7,  9, ),
    QfnCnf( 'WGHE-1',  0.8, 0.40, 4.0, 5.0, 2.70, 3.70, 0.50,  7, 10, ),
    QfnCnf( 'WLLE-1',  0.8, 0.40, 8.0, 8.0, 6.25, 6.25, 0.50, 17, 17, ),
    QfnCnf( 'WLLE-2',  0.8, 0.40, 8.0, 8.0, 6.60, 6.60, 0.50, 16, 16, ),
    QfnCnf( 'WMME',    0.8, 0.40, 9.0, 9.0, 7.25, 7.25, 0.50, 18, 18, ),
    QfnCnf( 'WMME-1',  0.8, 0.40, 9.0, 9.0, 7.25, 7.25, 0.50, 19, 19, ),
    QfnCnf( 'WNNE',    0.8, 0.40, 10., 10., 8.25, 8.25, 0.50, 22, 22, ),
    QfnCnf( 'WNNE-1',  0.8, 0.40, 10., 10., 6.90, 6.90, 0.50, 22, 22, ),
    QfnCnf( 'WKKE',    0.8, 0.40, 7.0, 7.0, 5.25, 5.25, 0.50, 14, 14, ),
    QfnCnf( 'WLLE',    0.8, 0.40, 8.0, 8.0, 6.25, 6.25, 0.50, 16, 16, ),
    QfnCnf( 'WRRE',    0.8, 0.40, 12., 12.,10.25,10.25, 0.50, 25, 25, ),
    QfnCnf( 'WRRE-1',  0.8, 0.40, 12., 12., 6.90, 6.90, 0.50, 25, 25, ),
    QfnCnf( 'WRRE-2',  0.8, 0.40, 12., 12.,10.25,10.25, 0.50, 27, 27, ),

]

def uuid(category: str, full_name: str, identifier: str) -> str:
    """
    Return a uuid for the specified pin.

    Params:
        category:
            For example 'cmp' or 'pkg'.
        full_name:
            For example "SOIC127P762X120-16".
        identifier:
            For example 'pad-1' or 'pin-13'.
    """
    key = '{}-{}-{}'.format(category, full_name, identifier).lower().replace(' ', '~')
    if key not in uuid_cache:
        uuid_cache[key] = str(uuid4())
    return uuid_cache[key]

def generate_pkg(
    dirpath: str,
    author: str,
    configs: Iterable[QfnCnf],
    pkgcat: str,
    version: str,
    create_date: Optional[str],
) -> None:
    category = 'pkg'
    for config in configs:
        lines = []

        full_name = config.ipc_name()
        full_description = config.description()

        def _uuid(identifier: str) -> str:
            return uuid(category, full_name, identifier)

        uuid_pkg = _uuid('pkg')
        uuid_pads = [_uuid('pad-{}'.format(p)) \
            for p in range(1, config.N + 1)]
        uuid_epad = _uuid('epad');

        print('Generating {}: {}'.format(full_name, uuid_pkg))

        # General info
        lines.append('(librepcb_package {}'.format(uuid_pkg))
        lines.append(' (name "{}")'.format(full_name))
        lines.append(' (description "{}\\n\\nGenerated with {}")'.format(full_description, generator))
        lines.append(' (keywords "")')
        lines.append(' (author "{}")'.format(author))
        lines.append(' (version "{}")'.format(version))
        lines.append(' (created {})'.format(create_date or now()))
        lines.append(' (deprecated false)')
        lines.append(' (category {})'.format(pkgcat))
        for p in range(1, config.N + 1):
            lines.append(' (pad {} (name "{}"))'.format(uuid_pads[p - 1], p))
        lines.append(
            ' (pad {} (name "{}"))'.format(uuid_epad, config.N + 1 ) );

        def add_footprint_variant(
            key: str,
            name: str,
            density_level: str,
        ) -> None:

            # UUIDs
            uuid_footprint = _uuid('footprint')
            uuid_silkscreen = [_uuid('polygon-silkscreen-{}-{}'.format(quadrant, key)) for quadrant in [1, 2, 3, 4]]
            uuid_outline = _uuid('polygon-outline-{}'.format(key))
            uuid_courtyard = _uuid('polygon-courtyard-{}'.format(key))
            uuid_text_name = _uuid('text-name-{}'.format(key))
            uuid_text_value = _uuid('text-value-{}'.format(key))

            # Pad excess according to IPC density levels
            #excess = config.excess_by_density(density_level)

            # Lead contact offsets
            #lead_contact_x_offset = config.lead_span_x / 2 - config.lead_contact_length  # this is the inner side of the contact area

            # Position of the first and last pad
            #pos_first = get_pad_coords(1, config.lead_count, config.pitch, lead_contact_x_offset)
            #pos_last = get_pad_coords(config.lead_count, config.lead_count, config.pitch, lead_contact_x_offset)

            lines.append(' (footprint {}'.format(uuid_footprint))
            lines.append('  (name "{}")'.format(name))
            lines.append('  (description "")')

            # Pads
            #pad_width = config.lead_width + excess.side * 2
            #pad_length = config.lead_contact_length + excess.heel + excess.toe
            for p in range(1, config.N + 1):
                pad_uuid = uuid_pads[p - 1]
                pos = config.get_pad_coords( p, density_level );
                pad_rotation = \
                    90.0 if pos.orientation == 'horizontal' else 0.0;
                lines.append('  (pad {} (side top) (shape rect)'.format(pad_uuid))
                lines.append(('   (position {} {}) (rotation {}) ' + \
                    '(size {} {}) (drill 0.0)').format(
                        ff(pos.x), ff(pos.y),
                        ff(pad_rotation), ff(pos.w), ff(pos.l),));
                lines.append('  )')
            lines.append( '  (pad {} (side top) (shape rect)'.format(
                uuid_epad ) );
            lines.append( ( '    (position 0.0 0.0) ' + \
                '(rotation 0.00) (size {} {}) (drill 0.0)' ).format(
                    ff( config.D2 ), ff( config.E2 ) ) );
            lines.append( '  )' );

            # Silkscreen: 1 per quadrant
            # (Quadrant 1 is at the top right, the rest follows CCW)
            # Draw right angles for all corners except pin one which
            # doesn't get a line on the pin one side.
            pin_ext_x, pin_ext_y = config.get_pin_extent(
                density_level );
            pin_ext_x += 0.15; # We want a bit of space between pads and
            pin_ext_y += 0.15; # silkscreens.
            full_ext_x = config.D / 2;
            full_ext_y = config.E / 2;
            if full_ext_x < pin_ext_x + line_width:
                full_ext_x = pin_ext_x + line_width;
            if full_ext_y < pin_ext_y + line_width:
                full_ext_y = pin_ext_y + line_width;
            for quadrant in [1, 2, 3, 4]:
                uuid = uuid_silkscreen[quadrant - 1]

                lines.append( \
                    '  (polygon {} (layer top_placement)'.format(uuid));
                lines.append(('   (width {}) (fill false) ' + \
                    '(grab_area false)').format(line_width));

                sign_x = 1 if quadrant in [1, 4] else -1
                sign_y = 1 if quadrant in [1, 2] else -1

                if quadrant == 2:
                    lines.append(('   (vertex (position {} {}) ' + \
                        '(angle 0.0))').format(
                            ff( sign_x * ( full_ext_x + \
                                line_width / 2 ) ),
                            ff( sign_y * ( full_ext_y + \
                                line_width / 2 ) ) ) );
                    lines.append(('   (vertex (position {} {}) ' + \
                        '(angle 0.0))').format(
                            ff( sign_x * ( pin_ext_x + \
                                line_width / 2 ) ),
                            ff( sign_y * ( full_ext_y + \
                                line_width / 2 ) ) ) );
                else:
                    lines.append(('   (vertex (position {} {}) ' + \
                        '(angle 0.0))').format(
                            ff( sign_x * ( full_ext_x + \
                                line_width / 2 ) ),
                            ff( sign_y * ( pin_ext_y + \
                                line_width / 2 ) ) ) );
                    lines.append(('   (vertex (position {} {}) ' + \
                        '(angle 0.0))').format(
                            ff( sign_x * ( full_ext_x + \
                                line_width / 2 ) ),
                            ff( sign_y * ( full_ext_y + \
                                line_width / 2 ) ) ) );
                    lines.append(('   (vertex (position {} {}) ' + \
                        '(angle 0.0))').format(
                            ff( sign_x * ( pin_ext_x + \
                                line_width / 2 ) ),
                            ff( sign_y * ( full_ext_y + \
                                line_width / 2 ) ) ) );
                lines.append('  )')

            # Documentation outline (fully inside body)
            outline_x_offset = config.D / 2 - line_width / 2
            outline_y_offset = config.E / 2 - line_width / 2
            lines.append('  (polygon {} (layer top_documentation)'.format(uuid_outline))
            lines.append('   (width {}) (fill false) (grab_area false)'.format(line_width))
            # Used for shorter code lines below :)
            oxo = ff(outline_x_offset)
            oyo = ff(outline_y_offset)
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(oxo, oyo))  # NE
            lines.append('   (vertex (position {} -{}) (angle 0.0))'.format(oxo, oyo))  # SE
            lines.append('   (vertex (position -{} -{}) (angle 0.0))'.format(oxo, oyo))  # SW
            lines.append('   (vertex (position -{} {}) (angle 0.0))'.format(oxo, oyo))  # NW
            lines.append('   (vertex (position {} {}) (angle 0.0))'.format(oxo, oyo))  # NE
            lines.append('  )')

            # Courtyard
            x_max = config.D / 2 + \
                J_T[density_level] + courtyard[density_level];
            y_max = config.E / 2 + \
                J_T[density_level] + courtyard[density_level];
            lines.append('  (polygon {} (layer {})'.format(uuid_courtyard, 'top_courtyard'))
            lines.append('   (width {}) (fill false) (grab_area false)'.format(COURTYARD_LINE_WIDTH))
            for ( x, y ) in [ ( 1, 1 ), ( 1, -1 ), ( -1, -1 ),
                    ( -1, 1 ), ( 1, 1 ) ]:
                xx = ff( x * x_max );
                yy = ff( y * y_max );
                lines.append(
                    '   (vertex (position {} {}) (angle 0.0))'.format(
                        xx, yy))
            lines.append('  )')

            # Labels
            y_offset = ff(config.E / 2 + text_y_offset)
            text_attrs = '(height {}) (stroke_width 0.2) ' \
                '(letter_spacing auto) (line_spacing auto)'.format(
                    pkg_text_height)
            lines.append(
                '  (stroke_text {} (layer top_names)'.format(
                    uuid_text_name))
            lines.append('   {}'.format(text_attrs))
            lines.append( ( '   (align center bottom) ' +
                '(position 0.0 {}) (rotation 0.0)' ).format(y_offset));
            lines.append( '   (auto_rotate true) (mirror false) ' +
                    '(value "{{NAME}}")')
            lines.append('  )')
            lines.append(
                '  (stroke_text {} (layer top_values)'.format(
                    uuid_text_value))
            lines.append('   {}'.format(text_attrs))
            lines.append( ( '   (align center top) ' +
                '(position 0.0 -{}) (rotation 0.0)' ).format(y_offset))
            lines.append( '   (auto_rotate true) (mirror false) ' +
                '(value "{{VALUE}}")')
            lines.append('  )')

            lines.append(' )')

        add_footprint_variant(
            'density~b', 'Density Level B (median protrusion)', 'B')
        add_footprint_variant(
            'density~a', 'Density Level A (max protrusion)', 'A')
        add_footprint_variant(
            'density~c', 'Density Level C (min protrusion)', 'C')

        lines.append(')')

        pkg_dir_path = path.join(dirpath, uuid_pkg)
        if not (path.exists(pkg_dir_path) and path.isdir(pkg_dir_path)):
            makedirs(pkg_dir_path)
        with open(path.join(pkg_dir_path, '.librepcb-pkg'), 'w') as f:
            f.write('0.1\n')
        with open(path.join(pkg_dir_path, 'package.lp'), 'w') as f:
            f.write('\n'.join(lines))
            f.write('\n')

if __name__ == '__main__':
    def _make(dirpath: str) -> None:
        if not (path.exists(dirpath) and path.isdir(dirpath)):
            makedirs(dirpath)
    _make('out')
    _make('out/qfn')
    _make('out/qfn/pkg')
    configs = list(chain.from_iterable(c.get_configs() for c in JEDEC_CONFIGS))
    generate_pkg(
        dirpath='out/qfn/pkg',
        author='Tom',
        configs=configs,
        pkgcat='e077449f-2272-41ce-92ce-0cb99dfa0697',
        version='0.3.1',
        create_date='2019-02-07T21:03:03Z',
    )
    save_cache(uuid_cache_file, uuid_cache)
