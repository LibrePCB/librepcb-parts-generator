"""
Generate only the 3D models for crystal packages
"""

from os import path

import cadquery as cq

from cadquery_helpers import StepAssembly, StepColor


def generate(
    name: str,
    lower_body_width: float,
    lower_body_length: float,
    lower_body_height: float,
    upper_body_width: float,
    upper_body_length: float,
    upper_body_height: float,
    body_chamfer: float,
    pad_width: float,
    pad_length: float,
    pad_height: float,
) -> None:
    print(f'Generating pkg 3D model "{name}"')

    assembly = StepAssembly(name)

    body_standoff = 0.03

    lower_body = (
        cq.Workplane('XY')
        .box(lower_body_length, lower_body_width, lower_body_height, centered=(True, True, False))
        .edges('|Z')
        .chamfer(body_chamfer)
        .edges('|X or |Y')
        .chamfer(0.05)
    )
    upper_body = (
        cq.Workplane('XY')
        .box(upper_body_length, upper_body_width, upper_body_height, centered=(True, True, False))
        .edges('|Z')
        .chamfer(body_chamfer)
        .edges('|X or |Y')
        .chamfer(0.05)
    )
    body = lower_body.union(upper_body)
    assembly.add_body(body, 'body', StepColor.IC_BODY, location=cq.Location((0, 0, body_standoff)))

    pad = cq.Workplane('XY').box(pad_length, pad_width, pad_height, centered=(True, True, False))
    assembly.add_body(
        pad,
        'pad-1',
        StepColor.LEAD_SMT,
        location=cq.Location(
            (-(lower_body_length / 2) + (pad_length / 2) - 0.03, 0, 0),
        ),
    )
    assembly.add_body(
        pad,
        'pad-2',
        StepColor.LEAD_SMT,
        location=cq.Location(
            ((lower_body_length / 2) - (pad_length / 2) + 0.03, 0, 0),
        ),
    )

    # Save without fusing for massively better minification!
    out_path = path.join('out_3d', 'crystal', f'{name}.step')
    assembly.save(out_path, fused=False)


if __name__ == '__main__':
    generate(
        name='ABM3',
        lower_body_width=3.2,
        lower_body_length=5.0,
        lower_body_height=0.5,  # guessed
        upper_body_width=2.8,  # guessed
        upper_body_length=4.4,  # guessed
        upper_body_height=1.3,
        body_chamfer=0.2,  # guessed
        pad_width=2.0,
        pad_length=1.3,
        pad_height=0.2,  # guessed
    )
