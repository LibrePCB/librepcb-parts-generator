"""
Generate only the 3D models for SOT packages
"""

from os import path

from typing import Iterable, Tuple

import cadquery as cq

from cadquery_helpers import StepAssembly, StepColor


def generate(
    name: str,
    body_width: float,
    body_length: float,
    total_height: float,
    lead_span: float,
    lead_height: float,
    lead_contact_length: float,
    leads_left: Iterable[Tuple[str, float, float]],
    leads_right: Iterable[Tuple[str, float, float]],
    pin1_indicator: bool,
) -> None:
    print(f'Generating pkg 3D model "{name}"')

    assembly = StepAssembly(name)

    body_standoff = 0.1
    body_height = total_height - body_standoff
    body_chamfer = 0.15
    dot_diameter = min(body_width * 0.25, 0.8)
    dot_position = dot_diameter
    dot_depth = 0.1
    lead_z_top = body_standoff + (body_height / 2)
    bend_radius = min(0.1 + (lead_height / 2), lead_contact_length / 3)

    dot_center = (
        -(body_width / 2) + dot_position,
        (body_length / 2) - dot_position,
        body_standoff + body_height - dot_depth,
    )

    body = (
        cq.Workplane('XY', origin=(0, 0, body_standoff + (body_height / 2)))
        .box(body_width, body_length, body_height)
        .edges()
        .chamfer(body_chamfer)
    )
    if pin1_indicator:
        body = body.workplane(
            origin=(dot_center[0], dot_center[1]), offset=(body_height / 2) - dot_depth
        ).cylinder(5, dot_diameter / 2, centered=(True, True, False), combine='cut')
    assembly.add_body(body, 'body', StepColor.IC_BODY)

    if pin1_indicator:
        dot = cq.Workplane('XY', origin=dot_center).cylinder(
            0.05, dot_diameter / 2, centered=(True, True, False)
        )
        assembly.add_body(dot, 'dot', StepColor.IC_PIN1_DOT)

    leads_by_width = dict()
    for x_sgn, rotation, leads in [(-1, 0, leads_left), (1, 180, leads_right)]:
        for lead_name, lead_y, lead_width in leads:
            if lead_width not in leads_by_width:
                lead_path = (
                    cq.Workplane('XZ')
                    .hLine(lead_contact_length - (lead_height / 2) - bend_radius)
                    .ellipseArc(
                        x_radius=bend_radius, y_radius=bend_radius, angle1=270, angle2=360, sense=1
                    )
                    .vLine(lead_z_top - lead_height - (2 * bend_radius))
                    .ellipseArc(
                        x_radius=bend_radius, y_radius=bend_radius, angle1=90, angle2=180, sense=-1
                    )
                    .hLine((lead_span / 2) - bend_radius - lead_contact_length + (lead_height / 2))
                )
                leads_by_width[lead_width] = (
                    cq.Workplane('ZY').rect(lead_height, lead_width).sweep(lead_path)
                )
            assembly.add_body(
                leads_by_width[lead_width],
                'lead-{}'.format(lead_name),
                StepColor.LEAD_SMT,
                location=cq.Location(
                    (
                        x_sgn * lead_span / 2,
                        lead_y,
                        lead_height / 2,
                    ),
                    (0, 0, 1),
                    rotation,
                ),
            )

    # Save without fusing for massively better minification!
    out_path = path.join('out_3d', 'sot', f'{name}.step')
    assembly.save(out_path, fused=False)


if __name__ == '__main__':
    generate(
        name='SOT223-4P230_700X180L175X75T175X300',
        body_width=3.5,
        body_length=6.5,
        total_height=1.8,
        lead_span=7.0,
        lead_height=0.27,
        lead_contact_length=0.9,
        leads_left=[
            ('1', 2.3, 0.7),
            ('2', 0, 0.7),
            ('3', -2.3, 0.7),
        ],
        leads_right=[
            ('4', 0, 3.0),
        ],
        pin1_indicator=True,
    )
    generate(
        name='SOT23-3P95_230X110L50X40',
        body_width=1.3,
        body_length=2.9,
        total_height=1.1,
        lead_span=2.3,
        lead_height=0.14,
        lead_contact_length=0.4,  # JEDEC says 0.5mm, but it looks impossible
        leads_left=[
            ('1', 0.95, 0.4),
            ('2', -0.95, 0.4),
        ],
        leads_right=[
            ('3', 0, 0.4),
        ],
        pin1_indicator=False,
    )
    generate(
        name='SOT23-3P95_280X145L60X40',
        body_width=1.6,
        body_length=2.9,
        total_height=1.45,
        lead_span=2.8,
        lead_height=0.17,
        lead_contact_length=0.45,
        leads_left=[
            ('1', 0.95, 0.4),
            ('2', -0.95, 0.4),
        ],
        leads_right=[
            ('3', 0, 0.4),
        ],
        pin1_indicator=False,
    )
    generate(
        name='SOT23-5P95_280X145L60X40',
        body_width=1.6,
        body_length=2.9,
        total_height=1.45,
        lead_span=2.8,
        lead_height=0.17,
        lead_contact_length=0.45,
        leads_left=[
            ('1', 0.95, 0.4),
            ('2', 0, 0.4),
            ('3', -0.95, 0.4),
        ],
        leads_right=[
            ('4', -0.95, 0.4),
            ('5', 0.95, 0.4),
        ],
        pin1_indicator=True,
    )
    generate(
        name='SOT23-6P95_280X145L60X40',
        body_width=1.6,
        body_length=2.9,
        total_height=1.45,
        lead_span=2.8,
        lead_height=0.17,
        lead_contact_length=0.45,
        leads_left=[
            ('1', 0.95, 0.4),
            ('2', 0, 0.4),
            ('3', -0.95, 0.4),
        ],
        leads_right=[
            ('4', -0.95, 0.4),
            ('5', 0, 0.4),
            ('6', 0.95, 0.4),
        ],
        pin1_indicator=True,
    )
    generate(
        name='SOT353-5P65_210X110L42X25',
        body_width=1.25,
        body_length=2.0,
        total_height=1.10,
        lead_span=2.1,
        lead_height=0.17,
        lead_contact_length=0.15 + 0.17,
        leads_left=[
            ('1', 0.65, 0.25),
            ('2', 0, 0.25),
            ('3', -0.65, 0.25),
        ],
        leads_right=[
            ('4', -0.65, 0.25),
            ('5', 0.65, 0.25),
        ],
        pin1_indicator=True,
    )
