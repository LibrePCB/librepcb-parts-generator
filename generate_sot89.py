"""
Generate only the 3D models for SOT-89 packages
"""

from os import path

import cadquery as cq

from cadquery_helpers import StepAssembly, StepColor


def generate(
    name: str,
    body_width: float,
    body_length: float,
    total_height: float,
    lead_length: float,
    lead_body_overlap: float,
    lead_width: float,
    lead_height: float,
    tab_length: float,
    tab_width_left: float,
    tab_width_right: float,
) -> None:
    print(f'Generating pkg 3D model "{name}"')

    assembly = StepAssembly(name)

    body_standoff = 0.03
    body_height = total_height - body_standoff
    body_chamfer = 0.1

    body = (
        cq.Workplane('XY', origin=(0, 0, body_standoff + (body_height / 2)))
        .box(body_width, body_length, body_height)
        .edges()
        .chamfer(body_chamfer)
    )
    assembly.add_body(body, 'body', StepColor.IC_BODY)

    lead = cq.Workplane('XY').box(
        lead_length + lead_body_overlap, lead_width, lead_height, centered=(False, True, False)
    )
    assembly.add_body(
        lead,
        'lead-1',
        StepColor.LEAD_SMT,
        location=cq.Location(
            (-(body_width / 2) - lead_length, 1.5, 0),
        ),
    )
    assembly.add_body(
        lead,
        'lead-3',
        StepColor.LEAD_SMT,
        location=cq.Location(
            (-(body_width / 2) - lead_length, -1.5, 0),
        ),
    )

    tab_center_offset = lead_length + (body_width / 2)
    tab = (
        cq.Workplane('XY')
        .box(
            lead_length + body_width + tab_length,
            tab_width_left,
            lead_height,
            centered=(False, True, False),
        )
        .workplane(origin=(tab_center_offset, 0), offset=0)
        .box(
            tab_length + body_width + lead_length - tab_center_offset,
            tab_width_right,
            lead_height,
            centered=(False, True, True),
            combine=True,
        )
        .workplane(origin=(tab_center_offset, 0), offset=0)
        .cylinder(lead_height, tab_width_right / 2, centered=(True, True, True), combine=True)
    )

    assembly.add_body(
        tab,
        'lead-2',
        StepColor.LEAD_SMT,
        location=cq.Location(
            (-(body_width / 2) - lead_length, 0, 0),
        ),
    )

    # Save without fusing for massively better minification!
    out_path = path.join('out_3d', 'sot89', f'{name}.step')
    assembly.save(out_path, fused=False)


if __name__ == '__main__':
    generate(
        name='SOT89-3',
        body_width=2.45,
        body_length=4.5,
        total_height=1.6,
        lead_length=1.045,
        lead_body_overlap=0.4,  # Not standardized, multiple variations exist
        lead_width=0.42,
        lead_height=0.395,
        tab_length=0.6,
        tab_width_left=0.5,
        tab_width_right=1.725,
    )
