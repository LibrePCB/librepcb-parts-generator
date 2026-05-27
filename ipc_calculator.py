import math
from dataclasses import dataclass

from typing import Optional

from common import Dimension


@dataclass(frozen=True)
class IpcSolderJointTable:
    toe: float
    heel: float
    side: float
    courtyard: float


@dataclass(frozen=True)
class IpcCalculatorResult:
    pad_pos_dx: float
    pad_size_x: float
    pad_size_y: float


class IpcCalculator:
    def __init__(
        self,
        lead_span: Dimension,
        terminal_length: Dimension,
        lead_space: Optional[Dimension],
        lead_width: Dimension,
        fabrication_tolerance: float = 0.0,
        placement_tolerance: float = 0.0,
    ):
        self.lead_span = lead_span
        self.terminal_length = terminal_length
        if lead_space is None:
            self.lead_space = Dimension.range(
                min=self.lead_span.min - 2 * self.terminal_length.max,
                max=self.lead_span.max - 2 * self.terminal_length.min,
            )
        else:
            self.lead_space = lead_space
        self.lead_width = lead_width
        self.fabrication_tolerance = fabrication_tolerance
        self.placement_tolerance = placement_tolerance
        assert self.lead_space.max < self.lead_span.min
        assert self.terminal_length.max < (self.lead_span.min / 2)

    def calculate(
        self, minmax_table: IpcSolderJointTable, nominal_table: IpcSolderJointTable
    ) -> IpcCalculatorResult:
        # Determine tables to use
        if (
            self.lead_span.is_nominal
            and self.lead_space.is_nominal
            and self.terminal_length.is_nominal
        ):
            x_table = nominal_table
        elif (
            not self.lead_span.is_nominal
            and not self.lead_space.is_nominal
            and not self.terminal_length.is_nominal
        ):
            x_table = minmax_table
        else:
            # Here I don't know which table we should use. But it seems that in
            # some cases it doesn't matter, so we can use any of those tables.
            # In case the tables are not identical, abort here.
            assert minmax_table.toe == nominal_table.toe
            assert minmax_table.heel == nominal_table.heel
            x_table = minmax_table
        y_table = nominal_table if self.lead_width.is_nominal else minmax_table
        # Calculate Tt
        toe_tolerance = math.sqrt(
            math.pow(self.lead_span.tolerance, 2)
            + math.pow(2 * self.fabrication_tolerance, 2)
            + math.pow(2 * self.placement_tolerance, 2)
        )
        # Calculate Zmax
        pad_span = self.lead_span.min + (2 * x_table.toe) + toe_tolerance
        # Calculate Stol(RMS)
        lead_space_tolerance_rms = math.sqrt(
            math.pow(self.lead_span.tolerance, 2) + 2 * math.pow(self.terminal_length.tolerance, 2)
        )
        # Calculate Sdiff
        lead_space_difference = self.lead_space.tolerance - lead_space_tolerance_rms
        # Calculate Smin(RMS) & Smax(RMS)
        lead_space_rms = Dimension.range(
            min=self.lead_space.min + (lead_space_difference / 2),
            max=self.lead_space.max - (lead_space_difference / 2),
        )
        # Calculate Ht
        heel_tolerance = math.sqrt(
            math.pow(lead_space_rms.max - lead_space_rms.min, 2)
            + math.pow(2 * self.fabrication_tolerance, 2)
            + math.pow(2 * self.placement_tolerance, 2)
        )
        # Calculate Gmin
        pad_space = lead_space_rms.max - (2 * x_table.heel) - heel_tolerance
        # Calculate pad size X
        pad_size_x = (pad_span - pad_space) / 2
        # Calculate pad size Y
        pad_size_y = self.lead_width.max + (2 * y_table.side)
        # Return results
        return IpcCalculatorResult(
            pad_pos_dx=(pad_span - pad_size_x) / 2,
            pad_size_x=pad_size_x,
            pad_size_y=pad_size_y,
        )


calculator = IpcCalculator(
    lead_span=Dimension(6.0),
    terminal_length=Dimension.plusminus(0.835, 0.435),
    lead_space=None,
    lead_width=Dimension.range(0.31, 0.51),
)


# Density Levels (pitch > 1.00mm)
DENSITY_LEVELS = [
    (
        'Least Density Level',
        IpcSolderJointTable(toe=0.3, heel=0.4, side=0.06, courtyard=0.1),
        IpcSolderJointTable(toe=0.3, heel=0.4, side=0.06, courtyard=0.1),
    ),
    (
        'Nominal Density Level',
        IpcSolderJointTable(toe=0.35, heel=0.5, side=0.08, courtyard=0.2),
        IpcSolderJointTable(toe=0.35, heel=0.5, side=0.08, courtyard=0.2),
    ),
    (
        'Most Density Level',
        IpcSolderJointTable(toe=0.4, heel=0.6, side=0.1, courtyard=0.4),
        IpcSolderJointTable(toe=0.4, heel=0.6, side=0.1, courtyard=0.4),
    ),
]

for lvl in DENSITY_LEVELS:
    print(lvl[0])

    res = calculator.calculate(lvl[1], lvl[2])
    print(f'  pad_size_x = {round(res.pad_size_x, 2)}')
    print(f'  pad_size_y = {round(res.pad_size_y, 2)}')
    print(f'  pad_dx = {round(res.pad_pos_dx, 2)}')
