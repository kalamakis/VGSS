from __future__ import annotations

import math

from .models import Bounds, DIRECTIONS


def directional_distances(a: Bounds, b: Bounds) -> dict[str, float]:
    """
    Calculate the six signed directional distances from A to B.

    Positive values represent a gap in the corresponding direction.
    Zero represents touching in that direction.
    Negative values represent overlap of the projected intervals.
    """

    return {
        "PX": b.xmin - a.xmax,
        "PY": b.ymin - a.ymax,
        "PZ": b.zmin - a.zmax,
        "NX": a.xmin - b.xmax,
        "NY": a.ymin - b.ymax,
        "NZ": a.zmin - b.zmax,
    }


def block_distance(a: Bounds, b: Bounds) -> float:
    """Definition 4.2: maximum of the six signed directional distances."""

    return max(directional_distances(a, b).values())


def limiting_directions(
    a: Bounds,
    b: Bounds,
    *,
    abs_tol: float = 1e-12,
) -> tuple[str, ...]:
    """
    Return every signed direction K for which d_K(A, B) = d(A, B).

    More than one direction can be returned when the maximum is tied.
    """

    distances = directional_distances(a, b)
    overall = max(distances.values())
    return tuple(
        direction
        for direction in DIRECTIONS
        if math.isclose(distances[direction], overall, abs_tol=abs_tol)
    )


def touches_or_overlaps(
    a: Bounds,
    b: Bounds,
    *,
    abs_tol: float = 1e-12,
) -> bool:
    """
    Return True when A and B touch or overlap as closed cuboids.

    For disjoint cuboids, Definition 4.2 gives a strictly positive value.
    """

    return block_distance(a, b) <= abs_tol


def boxes_touch(
    a: Bounds,
    b: Bounds,
    *,
    abs_tol: float = 1e-12,
) -> bool:
    """
    Return True only when two cuboids touch directly.

    Touching means:
        d(A, B) == 0

    This includes face, edge, and corner contact.
    """

    return math.isclose(
        block_distance(a, b),
        0.0,
        abs_tol=abs_tol,
    )


def boxes_overlap(
    a: Bounds,
    b: Bounds,
    *,
    abs_tol: float = 1e-12,
) -> bool:
    """
    Return True when two cuboids overlap.

    Overlap means:
        d(A, B) < 0
    """

    return block_distance(a, b) < -abs_tol
