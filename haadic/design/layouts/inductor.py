"""Functions to generate inductors. These functions can be used to create cells that can be exported as gds files."""

from numpy import tan, pi
from typing import Optional
import logging

from haadic.design.layouts.base_cell import BaseCell
import haadic.design.layouts.general as gen


def octagonal_inductor(
    layout: BaseCell,
    d_i: float,
    n_turn: int,
    width: float,
    gap: float,
    layer_nb: int = -1,
    pin_name: tuple[str, str] = ("P1", "P2"),
    port_ext: float = 15,
    port_gap: float = -1,
    bridge_nb: Optional[int] = None,
) -> BaseCell:
    """
    Generate a multi-turn octagonal inductor.

    :param layout: layout where the inductor will be drawn
    :param d_i: inner diameter in micron
    :param n_turn: number of turn
    :param width: width of the track
    :param gap: gap between the track
    :param pin_name: name of the two ports of the inductor (default "P1" and "P2")
    :param port_gap: gap between the two ports (default value : gap).
    :param port_ext: port extension outward the inductor (default value :µm)
    :param layer_nb: layer index for inductor core drawing.
    :param bridge_nb: layer index of the bridge (for multi-turn inductor).
    :return: pya.Cell of the inductor
    """
    m_top = layout.metal(layer_nb)
    if bridge_nb == 0:
        m_bridge = layout.pad
    else:
        m_bridge = layout.metal(bridge_nb or layer_nb - 1)

    # Convert units to database units (nm)
    p_ext = port_ext
    p_gap = gap + width if port_gap == -1 else port_gap + width
    b_gap = 2 * width + gap

    si = tan(pi / 8) / 2
    even_turn = n_turn % 2 == 0

    for i in range(n_turn):
        d_a = d_i + width + 2 * i * (width + gap)
        end = i == n_turn - 1
        start = i == 0
        logging.debug(
            f"{end=}\t{even_turn=} {0 if (not end) and even_turn else p_gap / 2}"
        )

        # Define path points in nm
        path = [
            (-i * (width + gap), 0 if (not end) and even_turn else p_gap / 2),
            (-i * (width + gap), d_a * si),
            (d_a * (0.5 - si) - i * (width + gap), d_a / 2),
            (d_a * (0.5 + si) - i * (width + gap), d_a / 2),
            (d_a - i * (width + gap), d_a * si),
            (
                d_a - i * (width + gap),
                b_gap / 2 if even_turn or not start else 0,
            ),
        ]

        if end:
            path.insert(0, (-p_ext, p_gap / 2))

        for j in (-1, 1):
            # Create path for top metal
            path_pts = [(x, j * y) for x, y in path]
            gen.add_path(layout, m_top, path_pts, width)

            if not start:
                if j == 1:
                    # Create connecting path
                    connect_pts = [
                        (path[-1][0], j * path[-1][1]),
                        (path[-1][0], path[-1][1] - width / 2),
                        (path[-1][0] - width - gap, -path[-1][1] + width / 2),
                        (path[-1][0] - width - gap, -path[-1][1]),
                    ]
                    gen.add_path(layout, m_top, connect_pts, width)
                else:
                    # Create bridge path
                    cross_pts = [
                        (path[-1][0], -path[-1][1] - width),
                        (path[-1][0], -path[-1][1] + width / 2),
                        (path[-1][0] - width - gap, path[-1][1] - width / 2),
                        (path[-1][0] - width - gap, path[-1][1] + width),
                    ]
                    gen.add_path(layout, m_bridge, cross_pts, width)

                    v1 = gen.via(layout, layer_nb - 1, (width, width))
                    layout.insert_cell(
                        v1, (path[-1][0] - 1.5 * width - gap, path[-1][1])
                    )
                    layout.insert_cell(
                        v1, (path[-1][0] - width / 2, -path[-1][1] - width)
                    )

    # Add port labels
    gen.add_text(layout, m_top, pin_name[0], (-p_ext, p_gap / 2))
    gen.add_text(layout, m_top, pin_name[1], (-p_ext, -p_gap / 2))
    return layout.flatten(-1, True)
