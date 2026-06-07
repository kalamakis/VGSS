from bgs.distances import block_distance, directional_distances, limiting_directions
from bgs.models import Bounds


def test_c1_to_c2_positive_x_gap() -> None:
    c1 = Bounds(0, 1, 0, 1, 0, 1)
    c2 = Bounds(3, 4, 0, 1, 0, 1)

    distances = directional_distances(c1, c2)

    assert distances == {
        "PX": 2,
        "PY": -1,
        "PZ": -1,
        "NX": -4,
        "NY": -1,
        "NZ": -1,
    }
    assert block_distance(c1, c2) == 2
    assert limiting_directions(c1, c2) == ("PX",)
