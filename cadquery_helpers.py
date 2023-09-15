from os import makedirs, path

from typing import Optional

import cadquery as cq
from OCP.Message import Message, Message_Gravity  # type: ignore


class StepConstants:
    THT_LEAD_SOLDER_LENGTH = 3.0  # Lead length on the PCB solder side


class StepColor:
    LEAD_SMT = cq.Color('gainsboro')
    LEAD_THT = cq.Color('gainsboro')


class StepAssembly:
    """
    A STEP assembly.
    """
    def __init__(self, name: str):
        self.assembly = cq.Assembly(name=name)

        # Less verbose output
        for printer in Message.DefaultMessenger_s().Printers():
            printer.SetTraceLevel(Message_Gravity.Message_Fail)

    def add_body(self, body: cq.Workplane, name: str, color: cq.Color,
                 location: Optional[cq.Location] = None) -> None:
        """
        Add a body to the assembly.

        Important: If the same body is added multiple times to the assembly
        with different transformations, please use the `location` parameter
        instead of transforming each body! This leads to much more efficient
        STEP minification.
        """
        self.assembly.add(body, name=name, color=color, loc=location)

    def save(self, out_path: str, fused: bool) -> None:
        """
        Write the STEP file to the specified path.

        Important: For simple bodies with (almost) no repetition (like
        resistors, capacitors, ...), pass `fused=True` to get a simple,
        non-hierarchical STEP file. However, for models with repetition (like
        an IC with several pins), pass `fused=False` since this leads to much
        more efficient STEP minification (saves several 100MB in total!).
        """
        dir_path = path.dirname(out_path)
        if path.exists(dir_path) and not path.isdir(dir_path):
            raise RuntimeError(f'Path "{dir_path}" exists but is not a directory')
        if not path.exists(dir_path):
            makedirs(dir_path)

        mode = 'fused' if fused else 'default'  # type: cq.occ_impl.exporters.assembly.STEPExportModeLiterals
        self.assembly.save(out_path, 'STEP', mode=mode, write_pcurves=False)
