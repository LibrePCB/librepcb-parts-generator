"""
Configuration file, containing all available DFN configs.

"""

# Maximal lead width as a function of pitch, Table 4
LEAD_WIDTH = {
        0.95: 0.45,
        0.8: 0.35,
        0.65: 0.35,
        0.5: 0.30,
        0.4: 0.25
    }


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
                 no_exp: bool = True,    # By default we create variants w/o exp
                 print_pad: bool = False,    # By default, the pad length is not in the full name
                 lead_width: float = None,
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


JEDEC_CONFIGS = [
        # Table 6
        # Square, 1.5 x 1.5
        DfnConfig(1.5, 1.5, 0.5, 4, 0.95, 1.00, 0.55, 0.70, 0.10),     # V1515D
        DfnConfig(1.5, 1.5, 0.5, 4, 0.75, 0.80, 0.55, 0.70, 0.10),     # W1515D
        # Square, 2.0 x 2.0
        DfnConfig(2.0, 2.0, 0.65, 6, 0.95, 1.00, 0.30, 1.58, 0.65),    # V2020C    -- no nominal exp_pad
        DfnConfig(2.0, 2.0, 0.5, 4, 0.95, 1.00, 0.55, 1.20, 0.60),     # V2020D-1
        DfnConfig(2.0, 2.0, 0.5, 4, 0.75, 0.80, 0.55, 1.20, 0.60),     # W2020D-1
        DfnConfig(2.0, 2.0, 0.5, 6, 0.95, 1.00, 0.40, 1.75, 0.80, no_exp=False),     # V2020D-4   -- no nominal exp_pad
        DfnConfig(2.0, 2.0, 0.5, 6, 0.75, 0.80, 0.40, 1.75, 0.80, no_exp=False),     # W2020D-4   -- no nominal exp_pad
        DfnConfig(2.0, 2.0, 0.5, 6, 0.95, 1.00, 0.55, 1.20, 0.60),     # V2020D-2
        DfnConfig(2.0, 2.0, 0.5, 6, 0.75, 0.80, 0.55, 1.20, 0.60),     # W2020D-2
        DfnConfig(2.0, 2.0, 0.5, 8, 0.95, 1.00, 0.30, 1.20, 0.60),     # V2020D-3
        # Square, 2.5 x 2.5
        DfnConfig(2.5, 2.5, 0.8, 6, 0.95, 1.00, 0.55, 1.50, 0.70),     # V2525B
        DfnConfig(2.5, 2.5, 0.8, 6, 0.75, 0.80, 0.55, 1.50, 0.70),     # W2525B
        DfnConfig(2.5, 2.5, 0.5, 6, 0.95, 1.00, 0.55, 1.70, 1.10),     # V2525D-1
        DfnConfig(2.5, 2.5, 0.5, 6, 0.75, 0.80, 0.55, 1.70, 1.10),     # W2525D-1
        DfnConfig(2.5, 2.5, 0.5, 8, 0.95, 1.00, 0.55, 1.70, 1.10),     # V2525D-2
        DfnConfig(2.5, 2.5, 0.5, 8, 0.75, 0.80, 0.55, 1.70, 1.10),     # W2525D-2
        # Square, 3.0 x 3.0
        DfnConfig(3.0, 3.0, 0.95, 6, 0.95, 1.00, 0.55, 1.50, 0.70),    # V3030A-1
        DfnConfig(3.0, 3.0, 0.95, 6, 0.95, 1.00, 0.55, 1.50, 1.20, no_exp=False),    # V3030A-2
        # no_exp above, as it would be the same as the V3030A-1 without exposed pad
        DfnConfig(3.0, 3.0, 0.95, 6, 0.75, 0.80, 0.55, 1.50, 1.20),    # W3030A-2
        DfnConfig(3.0, 3.0, 0.8, 6, 0.95, 1.00, 0.50, 2.20, 1.30),     # V3030B
        DfnConfig(3.0, 3.0, 0.8, 6, 0.75, 0.80, 0.55, 2.20, 1.30),     # W3030B
        DfnConfig(3.0, 3.0, 0.65, 8, 0.95, 1.00, 0.30, 2.25, 1.30),    # V3030C-1   -- no nominal exp_pad
        DfnConfig(3.0, 3.0, 0.65, 8, 0.95, 1.00, 0.40, 2.50, 1.75, no_exp=False),    # V3030C-2   -- no nominal exp_pad
        DfnConfig(3.0, 3.0, 0.65, 8, 0.75, 0.80, 0.40, 2.50, 1.75, no_exp=False),    # W3030C-2   -- no nominal exp_pad
        DfnConfig(3.0, 3.0, 0.5, 8, 0.95, 1.00, 0.55, 2.20, 1.60),     # V3030D-1
        DfnConfig(3.0, 3.0, 0.5, 8, 0.75, 0.80, 0.55, 2.00, 1.20),     # W3030D-1
        DfnConfig(3.0, 3.0, 0.5, 8, 0.95, 1.00, 0.40, 2.70, 1.75, no_exp=False),     # V3030D-4   -- no nominal exp_pad
        DfnConfig(3.0, 3.0, 0.5, 8, 0.75, 0.80, 0.40, 2.70, 1.75, no_exp=False),     # W3030D-4   -- no nominal exp_pad
        DfnConfig(3.0, 3.0, 0.5, 8, 0.95, 1.00, 0.55, 2.50, 1.50, no_exp=False),     # V3030D-6   -- no nominal exp_pad
        DfnConfig(3.0, 3.0, 0.5, 8, 0.75, 0.80, 0.55, 2.50, 1.50, no_exp=False),     # W3030D-6   -- no nominal exp_pad
        DfnConfig(3.0, 3.0, 0.5, 8, 0.95, 1.00, 0.45, 1.60, 1.60, no_exp=False),     # V3030D-7  -- no nominal pad length and exp_pad
        DfnConfig(3.0, 3.0, 0.5, 8, 0.75, 0.80, 0.45, 1.60, 1.60, no_exp=False),     # W3030D-7  -- no nominal pad length and exp_pad
        DfnConfig(3.0, 3.0, 0.5, 10, 0.95, 1.00, 0.55, 2.20, 1.60, print_pad=True),    # V3030D-2
        DfnConfig(3.0, 3.0, 0.5, 10, 0.75, 0.80, 0.55, 2.00, 1.20),    # W3030D-2
        DfnConfig(3.0, 3.0, 0.5, 10, 0.95, 1.00, 0.30, 2.20, 1.60, print_pad=True),    # V3030D-3
        DfnConfig(3.0, 3.0, 0.5, 10, 0.95, 1.00, 0.40, 2.70, 1.75, no_exp=False),    # V3030D-5   -- no nominal exp_pad
        DfnConfig(3.0, 3.0, 0.5, 10, 0.75, 0.80, 0.40, 2.70, 1.75, no_exp=False),    # W3030D-5   -- no nominal exp_pad
        # Square, 3.5 x 3.5
        DfnConfig(3.5, 3.5, 0.5, 10, 0.95, 1.00, 0.55, 2.70, 2.10),    # V3535D-1
        DfnConfig(3.5, 3.5, 0.5, 10, 0.75, 0.80, 0.55, 2.70, 2.10),    # W3535D-1
        DfnConfig(3.5, 3.5, 0.5, 12, 0.95, 1.00, 0.55, 2.70, 2.10),    # V3535D-2
        DfnConfig(3.5, 3.5, 0.5, 12, 0.75, 0.80, 0.55, 2.70, 2.10),    # W3535D-2
        # Square, 4.0 x 4.0
        DfnConfig(4.0, 4.0, 0.8, 8, 0.95, 1.00, 0.55, 3.00, 2.20),     # V4040B
        DfnConfig(4.0, 4.0, 0.8, 8, 0.75, 0.80, 0.55, 3.00, 2.20),     # W4040B
        DfnConfig(4.0, 4.0, 0.65, 10, 0.95, 1.00, 0.40, 3.50, 2.80, no_exp=False),   # V4040C -- no nominal exp_pad
        DfnConfig(4.0, 4.0, 0.65, 10, 0.75, 0.80, 0.40, 3.50, 2.80, no_exp=False),   # W4040C -- no nominal exp_pad
        DfnConfig(4.0, 4.0, 0.5, 10, 0.95, 1.00, 0.55, 3.20, 2.60),    # V4040D-1
        DfnConfig(4.0, 4.0, 0.5, 10, 0.75, 0.80, 0.55, 3.00, 2.20),    # W4040D-1
        DfnConfig(4.0, 4.0, 0.5, 12, 0.95, 1.00, 0.55, 3.20, 2.60),    # V4040D-2
        DfnConfig(4.0, 4.0, 0.5, 12, 0.75, 0.80, 0.55, 3.00, 2.20),    # W4040D-2
        DfnConfig(4.0, 4.0, 0.5, 14, 0.95, 1.00, 0.55, 3.20, 2.60),    # V4040D-3
        DfnConfig(4.0, 4.0, 0.5, 14, 0.75, 0.80, 0.55, 3.00, 2.20),    # W4040D-3
        # Square, 5.0 x 5.0
        DfnConfig(5.0, 5.0, 0.8, 8, 0.95, 1.00, 0.55, 4.00, 3.20),     # V5050B
        DfnConfig(5.0, 5.0, 0.8, 8, 0.75, 0.80, 0.55, 4.00, 3.20),     # W5050B
        DfnConfig(5.0, 5.0, 0.5, 16, 0.95, 1.00, 0.55, 4.20, 3.60),    # V5050D-1
        DfnConfig(5.0, 5.0, 0.5, 16, 0.75, 0.80, 0.55, 4.00, 3.20),    # W5050D-1
        DfnConfig(5.0, 5.0, 0.5, 18, 0.95, 1.00, 0.55, 4.20, 3.60),    # V5050D-2
        DfnConfig(5.0, 5.0, 0.5, 18, 0.75, 0.80, 0.55, 4.00, 3.20),    # W5050D-2
        # Table 6
        # Rectangular, Type 1, 2.0 x 2.5
        DfnConfig(2.0, 2.5, 0.8, 4, 0.95, 1.00, 0.55, 1.00, 0.70),     # V2025B
        DfnConfig(2.0, 2.5, 0.8, 4, 0.75, 0.80, 0.55, 1.00, 0.70),     # W2025B
        DfnConfig(2.0, 2.5, 0.5, 6, 0.95, 1.00, 0.55, 1.00, 0.70),     # V2025D-1
        DfnConfig(2.0, 2.5, 0.5, 6, 0.75, 0.80, 0.55, 1.00, 0.70),     # W2025D-1
        DfnConfig(2.0, 2.5, 0.5, 8, 0.95, 1.00, 0.55, 1.10, 0.80),     # V2025D-2 -- no nominal exp_pad
        DfnConfig(2.0, 2.5, 0.5, 8, 0.75, 0.80, 0.55, 1.10, 0.80),     # W2025D-2 -- no nominal exp_pad
        # Rectangular, Type 1, 2.0 x 3.0
        DfnConfig(2.0, 3.0, 0.5, 6, 0.95, 1.00, 0.40, 1.00, 1.20, no_exp=False),     # V2030D-1 -- no nominal exp_pad
        DfnConfig(2.0, 3.0, 0.5, 6, 0.75, 0.80, 0.40, 1.00, 1.20, no_exp=False),     # W2030D-1 -- no nominal exp_pad
        DfnConfig(2.0, 3.0, 0.5, 8, 0.95, 1.00, 0.40, 1.75, 1.90, no_exp=False),     # V2030D-2 -- no nominal exp_pad
        DfnConfig(2.0, 3.0, 0.5, 8, 0.75, 0.80, 0.40, 1.75, 1.90, no_exp=False),     # W2030D-2 -- no nominal exp_pad
        DfnConfig(2.0, 3.0, 0.5, 8, 0.95, 1.00, 0.45, 1.60, 1.60, no_exp=False),     # V2030D-3 -- no nominal pad length and exp_pad
        DfnConfig(2.0, 3.0, 0.5, 8, 0.75, 0.80, 0.45, 1.60, 1.60, no_exp=False),     # W2030D-3 -- no nominal pad length and exp_pad
        DfnConfig(2.0, 3.0, 0.5, 8, 0.55, 0.65, 0.45, 1.60, 1.60, no_exp=False),     # U2030D   -- no nominal pad length and exp_pad
        # Rectangular, Type 1, 2.5 x 3.0
        DfnConfig(2.5, 3.0, 0.8, 6, 0.95, 1.00, 0.55, 1.50, 1.20),     # V2530B
        DfnConfig(2.5, 3.0, 0.8, 6, 0.75, 0.80, 0.55, 1.50, 1.20),     # W2530B
        DfnConfig(2.5, 3.0, 0.5, 8, 0.95, 1.00, 0.55, 1.50, 1.20),     # V2530D
        DfnConfig(2.5, 3.0, 0.5, 8, 0.75, 0.80, 0.55, 1.50, 1.20),     # W2530D
        # Rectangular, Type 1, 3.0 x 4.0
        DfnConfig(3.0, 4.0, 0.8, 6, 0.95, 1.00, 0.55, 2.00, 2.20),     # V3040B
        DfnConfig(3.0, 4.0, 0.8, 6, 0.75, 0.80, 0.55, 2.00, 2.20),     # W3040B
        DfnConfig(3.0, 4.0, 0.5, 10, 0.95, 1.00, 0.55, 2.00, 2.20),    # V3040D
        DfnConfig(3.0, 4.0, 0.5, 10, 0.75, 0.80, 0.55, 2.00, 2.20),    # W3040D
        # Rectangular, Type 1, 4.0 x 5.0
        DfnConfig(4.0, 5.0, 0.8, 10, 0.95, 1.00, 0.55, 3.00, 3.20),    # V4050B
        DfnConfig(4.0, 5.0, 0.8, 10, 0.75, 0.80, 0.55, 3.00, 3.20),    # W4050B
        DfnConfig(4.0, 5.0, 0.5, 14, 0.95, 1.00, 0.55, 3.00, 3.20),    # V4050D
        DfnConfig(4.0, 5.0, 0.5, 14, 0.75, 0.80, 0.55, 3.00, 3.20),    # W4050D
        # Table 7
        # Rectangular, Type 2, 1.5 x 1.0
        DfnConfig(1.5, 1.0, 0.5, 4, 0.95, 1.00, 0.30, 0.00, 0.00),     # V1510D
        DfnConfig(1.5, 1.0, 0.5, 4, 0.75, 0.80, 0.30, 0.00, 0.00),     # W1510D
        # Rectangular, Type 2, 2.0 x 1.0
        DfnConfig(2.0, 1.0, 0.5, 4, 0.95, 1.00, 0.30, 0.00, 0.00),     # V2010D-1
        DfnConfig(2.0, 1.0, 0.5, 4, 0.75, 0.80, 0.30, 0.00, 0.00),     # W2010D-1
        DfnConfig(2.0, 1.0, 0.5, 6, 0.95, 1.00, 0.30, 0.00, 0.00),     # V2010D-2
        DfnConfig(2.0, 1.0, 0.5, 6, 0.75, 0.80, 0.30, 0.00, 0.00),     # W2010D-2
        # Rectangular, Type 2, 2.0 x 1.5
        DfnConfig(2.0, 1.5, 0.5, 4, 0.95, 1.00, 0.55, 1.20, 0.10),     # V2015D-1
        DfnConfig(2.0, 1.5, 0.5, 4, 0.75, 0.80, 0.55, 1.20, 0.10),     # W2015D-1
        DfnConfig(2.0, 1.5, 0.5, 6, 0.95, 1.00, 0.55, 1.20, 0.10),     # V2015D-2
        DfnConfig(2.0, 1.5, 0.5, 6, 0.75, 0.80, 0.55, 1.20, 0.10),     # W2015D-2
        # Rectangular, Type 2, 2.5 x 1.5
        DfnConfig(2.5, 1.5, 0.5, 6, 0.95, 1.00, 0.55, 1.70, 0.10),     # V2515D-1
        DfnConfig(2.5, 1.5, 0.5, 6, 0.75, 0.80, 0.55, 1.70, 0.10),     # W2515D-1
        DfnConfig(2.5, 1.5, 0.5, 8, 0.95, 1.00, 0.55, 1.70, 0.10),     # V2515D-2
        DfnConfig(2.5, 1.5, 0.5, 8, 0.75, 0.80, 0.55, 1.70, 0.10),     # W2515D-2
        # Rectangular, Type 2, 2.5 x 2.0
        DfnConfig(2.5, 2.0, 0.5, 4, 0.95, 1.00, 0.55, 1.70, 0.60),     # V2520D-1
        DfnConfig(2.5, 2.0, 0.5, 4, 0.75, 0.80, 0.55, 1.70, 0.60),     # W2520D-1
        DfnConfig(2.5, 2.0, 0.5, 6, 0.95, 1.00, 0.55, 1.70, 0.60),     # V2520D-2
        DfnConfig(2.5, 2.0, 0.5, 6, 0.75, 0.80, 0.55, 1.70, 0.60),     # W2520D-2
        DfnConfig(2.5, 2.0, 0.5, 8, 0.95, 1.00, 0.55, 1.70, 0.60),     # V2520D-3
        DfnConfig(2.5, 2.0, 0.5, 8, 0.75, 0.80, 0.55, 1.70, 0.60),     # W2520D-3
        # Rectangular, Type 2, 3.0 x 1.5
        DfnConfig(3.0, 1.5, 0.5, 8, 0.95, 1.00, 0.55, 2.20, 0.10),     # V3015D-1
        DfnConfig(3.0, 1.5, 0.5, 8, 0.75, 0.80, 0.55, 2.20, 0.10),     # W3015D-1
        DfnConfig(3.0, 1.5, 0.5, 10, 0.95, 1.00, 0.55, 2.20, 0.10),    # W3015D-2
        DfnConfig(3.0, 1.5, 0.5, 10, 0.75, 0.80, 0.55, 2.20, 0.10),    # W3015D-2
        # Rectangular, Type 2, 3.0 x 2.0
        DfnConfig(3.0, 2.0, 0.95, 6, 0.95, 1.00, 0.30, 2.20, 0.60),    # V3020A -- no nominal exp_pad, using manual values
        DfnConfig(3.0, 2.0, 0.65, 8, 0.95, 1.00, 0.30, 2.20, 0.60),    # V3020C -- no nominal exp_pad, using manual values
        DfnConfig(3.0, 2.0, 0.5, 8, 0.95, 1.00, 0.55, 2.20, 0.60),     # V3020D-1
        DfnConfig(3.0, 2.0, 0.5, 8, 0.75, 0.80, 0.55, 2.20, 0.60),     # W3020D-1
        DfnConfig(3.0, 2.0, 0.5, 8, 0.95, 1.00, 0.40, 2.20, 0.60, no_exp=False),     # V3020D-4 -- no nominal exp_pad
        DfnConfig(3.0, 2.0, 0.5, 8, 0.75, 0.80, 0.40, 2.20, 0.60, no_exp=False),     # W3020D-4 -- no nominal exp_pad
        DfnConfig(3.0, 2.0, 0.5, 10, 0.95, 1.00, 0.55, 2.20, 0.60, print_pad=True),    # V3020D-2
        DfnConfig(3.0, 2.0, 0.5, 10, 0.75, 0.80, 0.55, 2.20, 0.60),    # W3020D-2
        DfnConfig(3.0, 2.0, 0.5, 10, 0.95, 1.00, 0.30, 2.20, 0.60, print_pad=True),    # V3020D-3
        # Rectangular, Type 2, 3.0 x 2.5
        DfnConfig(3.0, 2.5, 0.5, 8, 0.95, 1.00, 0.55, 2.20, 1.10),     # V3025D-1
        DfnConfig(3.0, 2.5, 0.5, 8, 0.75, 0.80, 0.55, 2.20, 1.10),     # V3025D-1
        DfnConfig(3.0, 2.5, 0.5, 10, 0.95, 1.00, 0.50, 2.20, 1.10),    # V3025D-2
        DfnConfig(3.0, 2.5, 0.5, 10, 0.75, 0.80, 0.50, 2.20, 1.10),    # V3025D-2
        # Rectangular, Type 2, 3.5 x 2.5
        DfnConfig(3.5, 2.5, 0.5, 10, 0.95, 1.00, 0.55, 2.70, 1.10),    # V3525D-1
        DfnConfig(3.5, 2.5, 0.5, 10, 0.75, 0.80, 0.55, 2.70, 1.10),    # W3525D-1
        DfnConfig(3.5, 2.5, 0.5, 12, 0.95, 1.00, 0.55, 2.70, 1.10),    # V3525D-2
        DfnConfig(3.5, 2.5, 0.5, 12, 0.75, 0.80, 0.55, 2.70, 1.10),    # W3525D-2
        # Rectangular, Type 2, 3.5 x 3.0
        DfnConfig(3.5, 3.0, 0.5, 10, 0.95, 1.00, 0.55, 2.70, 1.60),    # V3530D-1
        DfnConfig(3.5, 3.0, 0.5, 10, 0.75, 0.80, 0.55, 2.70, 1.60),    # W3530D-1
        DfnConfig(3.5, 3.0, 0.5, 12, 0.95, 1.00, 0.55, 2.70, 1.60),    # V3530D-2
        DfnConfig(3.5, 3.0, 0.5, 12, 0.75, 0.80, 0.55, 2.70, 1.60),    # W3530D-2
        # Rectangular, Type 2, 4.0 x 3.0
        DfnConfig(4.0, 3.0, 0.5, 10, 0.95, 1.00, 0.55, 3.20, 1.60),    # V4030D-1
        DfnConfig(4.0, 3.0, 0.5, 10, 0.75, 0.80, 0.55, 3.20, 1.60),    # W4030D-1
        DfnConfig(4.0, 3.0, 0.5, 12, 0.95, 1.00, 0.55, 3.20, 1.60),    # V4030D-2
        DfnConfig(4.0, 3.0, 0.5, 12, 0.75, 0.80, 0.55, 3.20, 1.60),    # W4030D-2
        DfnConfig(4.0, 3.0, 0.5, 12, 0.95, 1.00, 0.40, 3.70, 1.80, no_exp=False),    # V4030D-4 -- no nominal exp_pad
        DfnConfig(4.0, 3.0, 0.5, 12, 0.75, 0.80, 0.40, 3.70, 1.80, no_exp=False),    # W4030D-4 -- no nominal exp_pad
        DfnConfig(4.0, 3.0, 0.5, 14, 0.95, 1.00, 0.55, 3.20, 1.60),    # V4030D-3
        DfnConfig(4.0, 3.0, 0.5, 14, 0.75, 0.80, 0.55, 3.20, 1.60),    # W4030D-3
        # Rectangular, Type 2, 5.0 x 3.0
        DfnConfig(5.0, 3.0, 0.5, 16, 0.95, 1.00, 0.55, 4.20, 1.60),    # V5030D-1
        DfnConfig(5.0, 3.0, 0.5, 16, 0.75, 0.80, 0.55, 4.20, 1.60),    # W5030D-1
        DfnConfig(5.0, 3.0, 0.5, 18, 0.95, 1.00, 0.55, 4.20, 1.60),    # V5030D-2
        DfnConfig(5.0, 3.0, 0.5, 18, 0.75, 0.80, 0.55, 4.20, 1.60),    # W5030D-2
        # Rectangular, Type 2, 5.0 x 4.0
        DfnConfig(5.0, 4.0, 0.5, 14, 0.95, 1.00, 0.55, 4.20, 2.60),    # V5040D-1
        DfnConfig(5.0, 4.0, 0.5, 14, 0.75, 0.80, 0.55, 4.20, 2.60),    # W5040D-1
        DfnConfig(5.0, 4.0, 0.5, 16, 0.95, 1.00, 0.55, 4.20, 2.60),    # V5040D-2
        DfnConfig(5.0, 4.0, 0.5, 16, 0.75, 0.80, 0.55, 4.20, 2.60),    # W5040D-2
        DfnConfig(5.0, 4.0, 0.5, 18, 0.95, 1.00, 0.55, 4.20, 2.60),    # V5040D-3
        DfnConfig(5.0, 4.0, 0.5, 18, 0.75, 0.80, 0.55, 4.20, 2.60),    # W5040D-3
        # Rectangular, Type 2, 6.0 x 5.0
        DfnConfig(6.0, 5.0, 0.5, 16, 0.95, 1.00, 0.55, 4.70, 3.40, no_exp=False),    # V6050D-1 -- no nominal exp_pad
        DfnConfig(6.0, 5.0, 0.5, 16, 0.75, 0.80, 0.55, 4.70, 3.40, no_exp=False),    # W6050D-1 -- no nominal exp_pad
        DfnConfig(6.0, 5.0, 0.5, 18, 0.95, 1.00, 0.55, 4.70, 3.40, no_exp=False),    # V6050D-2 -- no nominal exp_pad
        DfnConfig(6.0, 5.0, 0.5, 18, 0.75, 0.80, 0.55, 4.70, 3.40, no_exp=False),    # W6050D-2 -- no nominal exp_pad
    ]

THIRD_CONFIGS = [
        # Sensirion SHTC-3
        DfnConfig(2.0, 2.0, 1.0, 4, 0.75, 0.80, 0.35, 1.60, 0.70, lead_width=0.35),
    ]
