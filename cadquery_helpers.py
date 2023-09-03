from os import makedirs, path

import cadquery as cq
from OCP.Message import Message, Message_Gravity  # type: ignore


class StepAssembly:
    """
    A STEP assembly.
    """
    def __init__(self, name: str):
        self.assembly = cq.Assembly(name=name)

        # Less verbose output
        for printer in Message.DefaultMessenger_s().Printers():
            printer.SetTraceLevel(Message_Gravity.Message_Fail)

    def add_body(self, body: cq.Workplane, name: str, color: cq.Color) -> None:
        """
        Add a body to the assembly.
        """
        self.assembly.add(body, name=name, color=color)

    def save(self, out_path: str) -> None:
        """
        Write the STEP file to the specified path.
        """
        dir_path = path.dirname(out_path)
        if path.exists(dir_path) and not path.isdir(dir_path):
            raise RuntimeError(f'Path "{dir_path}" exists but is not a directory')
        if not path.exists(dir_path):
            makedirs(dir_path)

        self.assembly.save(out_path, 'STEP', mode='fused', write_pcurves=False)
