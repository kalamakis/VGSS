import numpy as np
import pytest

from bgs.models import Bounds, Conductor
from bgs.topology import InvalidConductorGeometryError, find_touching_nets


def conductor(name: str, bounds: Bounds) -> Conductor:
    return Conductor(name, bounds, np.zeros((6, 4, 3), dtype=float))


def test_face_edge_and_corner_contacts_form_one_connected_net() -> None:
    c1 = conductor("C1", Bounds(0, 1, 0, 1, 0, 1))
    c2 = conductor("C2", Bounds(1, 2, 0, 1, 0, 1))  # face contact
    c3 = conductor("C3", Bounds(2, 3, 1, 2, 0, 1))  # edge contact with C2
    c4 = conductor("C4", Bounds(3, 4, 2, 3, 1, 2))  # corner contact with C3
    c5 = conductor("C5", Bounds(8, 9, 8, 9, 8, 9))  # separate net

    nets = find_touching_nets([c1, c2, c3, c4, c5])

    assert [net.conductor_names for net in nets] == [
        ("C1", "C2", "C3", "C4"),
        ("C5",),
    ]


def test_overlapping_conductors_are_invalid_input() -> None:
    c1 = conductor("C1", Bounds(0, 2, 0, 2, 0, 2))
    c2 = conductor("C2", Bounds(1, 3, 1, 3, 1, 3))

    with pytest.raises(InvalidConductorGeometryError, match="overlap"):
        find_touching_nets([c1, c2])
