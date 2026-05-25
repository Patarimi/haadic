from numpy import tan, pi
from typing import Optional, Self, Any
import logging

import klayout.db as db

from .tools import LayerStack
from .general import via


class Path(list):
    def __new__(cls, value: Any) -> Self:
        return super().__new__(cls, list([(int(x), int(y)) for x, y in value]))  # ty: ignore too-many-positional-arguments


def octagonal_inductor(
    layout: db.Layout,
    d_i: float,
    n_turn: int,
    width: float,
    gap: float,
    layer_stack: LayerStack,
    layer_nb: int = -1,
    pin_name: tuple[str, str] = ("P1", "P2"),
    port_ext: float = 15e-6,
    port_gap: float = -1,
    bridge_nb: Optional[int] = None,
) -> db.Cell:
    """Generate a multi-turn octagonal inductor.
    
    :param layout: layout where the inductor will be drawn
    :param d_i: inner diameter in micron
    :param n_turn: number of turn
    :param width: width of the track
    :param gap: gap between the track
    :param layer_stack: the inductor will be drawn on the highest layer of the stack.
    :param pin_name: name of the two ports of the inductor (default "P1" and "P2")
    :param port_gap: gap between the two ports (default value : gap).
    :param port_ext: port extension outward the inductor (default value :µm)
    :param layer_nb: layer index for inductor core drawing.
    :param bridge_nb: layer index of the bridge (for multi-turn inductor).
    :return: pya.Cell of the inductor
    """
    m_top = layer_stack.get_metal_layer(layer_nb)
    if bridge_nb == 0:
        m_bridge = layer_stack.get_pad_layer()
    else:
        m_bridge = layer_stack.get_metal_layer(
            layer_nb - 1 if bridge_nb is None else bridge_nb
        )

    ind = layout.create_cell("ind")

    # Get layer info
    top_layer = layout.layer(m_top.layer, m_top.datatype)
    bridge_layer = layout.layer(m_bridge.layer, m_bridge.datatype)

    # Convert units to database units (nm)
    dbu = layout.dbu = 0.005  # 5 nm
    w_dbu = int(width * 1e6 / dbu)
    g_dbu = int(gap * 1e6 / dbu)
    d_i_dbu = int(d_i * 1e6 / dbu)
    p_ext_dbu = int(port_ext * 1e6 / dbu)
    p_gap_dbu = g_dbu + w_dbu if port_gap == -1 else int(port_gap * 1e6 / dbu) + w_dbu
    b_gap_dbu = 2 * w_dbu + g_dbu

    si = tan(pi / 8) / 2
    even_turn = n_turn % 2 == 0

    for i in range(n_turn):
        d_a_dbu = d_i_dbu + w_dbu + 2 * i * (w_dbu + g_dbu)
        end = i == n_turn - 1
        start = i == 0
        logging.debug(
            f"{end=}\t{even_turn=} {0 if (not end) and even_turn else p_gap_dbu / 2}"
        )

        # Define path points in nm
        path = Path(
            [
                (-i * (w_dbu + g_dbu), 0 if (not end) and even_turn else p_gap_dbu / 2),
                (-i * (w_dbu + g_dbu), d_a_dbu * si),
                (d_a_dbu * (0.5 - si) - i * (w_dbu + g_dbu), d_a_dbu / 2),
                (d_a_dbu * (0.5 + si) - i * (w_dbu + g_dbu), d_a_dbu / 2),
                (d_a_dbu - i * (w_dbu + g_dbu), d_a_dbu * si),
                (
                    d_a_dbu - i * (w_dbu + g_dbu),
                    b_gap_dbu / 2 if even_turn or not start else 0,
                ),
            ]
        )

        if end:
            path.insert(0, (-p_ext_dbu, p_gap_dbu / 2))

        for j in (-1, 1):
            # Create path for top metal
            path_pts = [db.Point(int(x), int(j * y)) for x, y in path]
            path_obj = db.Path(path_pts, w_dbu).polygon()
            ind.shapes(top_layer).insert(path_obj)

            if not start:
                if j == 1:
                    # Create connecting path
                    connect_pts = [
                        db.Point(path[-1][0], j * path[-1][1]),
                        db.Point(int(path[-1][0]), int(path[-1][1] - w_dbu / 2)),
                        db.Point(
                            int(path[-1][0] - w_dbu - g_dbu),
                            int(-path[-1][1] + w_dbu / 2),
                        ),
                        db.Point(int(path[-1][0] - w_dbu - g_dbu), int(-path[-1][1])),
                    ]
                    connect_path = db.Path(connect_pts, w_dbu).polygon()
                    ind.shapes(top_layer).insert(connect_path)
                else:
                    # Create bridge path
                    cross_pts = [
                        db.Point(int(path[-1][0]), int(-path[-1][1] - w_dbu)),
                        db.Point(int(path[-1][0]), int(-path[-1][1] + w_dbu / 2)),
                        db.Point(
                            int(path[-1][0] - w_dbu - g_dbu),
                            int(path[-1][1] - w_dbu / 2),
                        ),
                        db.Point(
                            int(path[-1][0] - w_dbu - g_dbu), int(path[-1][1] + w_dbu)
                        ),
                    ]
                    cross_path = db.Path(cross_pts, w_dbu).polygon()
                    ind.shapes(bridge_layer).insert(cross_path)

                    # Add vias
                    via_layer = layer_stack.get_via_layer(layer_nb - 1)
                    v1 = via(layout, via_layer, (w_dbu * dbu, w_dbu * dbu))
                    # Place vias
                    t1 = db.Trans(
                        int(path[-1][0] - 1.5 * w_dbu - g_dbu), int(path[-1][1])
                    )
                    t2 = db.Trans(
                        int(path[-1][0] - w_dbu / 2), int(-path[-1][1] - w_dbu)
                    )
                    ind.insert(db.CellInstArray(v1.cell_index(), t1))
                    ind.insert(db.CellInstArray(v1.cell_index(), t2))

    # Add port labels
    text_p1 = db.Text(pin_name[0], int(-p_ext_dbu), int(p_gap_dbu / 2))
    text_p1.halign = db.Text.HAlignCenter
    text_p1.valign = db.Text.VAlignCenter
    text_p2 = db.Text(pin_name[1], int(-p_ext_dbu), int(-p_gap_dbu / 2))
    text_p2.halign = db.Text.HAlignCenter
    text_p2.valign = db.Text.VAlignCenter
    ind.shapes(top_layer).insert(text_p1)
    ind.shapes(top_layer).insert(text_p2)
    ind.flatten(-1, True)
    return ind
