from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterable

from .distances import (
    block_distance,
    directional_distances,
    limiting_directions,
    touches_or_overlaps,
)
from .models import Bounds, Conductor, DIRECTIONS, GaussianSurface, make_surface_faces


class UnsupportedGeometryError(ValueError):
    """Raised for a geometry case intentionally deferred to a later milestone."""


@dataclass(frozen=True)
class PairwiseDistanceRow:
    other_conductor: str
    signed_distances: dict[str, float]
    overall_distance: float
    limiting_directions: tuple[str, ...]


@dataclass(frozen=True)
class BGSGenerationResult:
    master: Conductor
    gaussian_surface: GaussianSurface
    initial_extents: dict[str, float]
    final_extents: dict[str, float]
    cap_distance: float
    pairwise_rows: tuple[PairwiseDistanceRow, ...]
    used_isolated_fallback: bool


def _unsupported_touch_message(master: Conductor, other: Conductor) -> str:
    return (
        f"{master.name} and {other.name} touch or overlap. "
        "The current milestone does not merge blocks belonging to one physical "
        "conductor, so this BGS is skipped."
    )


def generate_bgs(
    master: Conductor,
    all_conductors: Iterable[Conductor],
    *,
    scale_factor: float = 1.0,
    max_distance: float = 10.0,
    touch_policy: str = "skip",
) -> BGSGenerationResult | None:
    """
    Generate a cuboid BGS using the conductor-only portion of Algorithm 4.2.

    Dielectric constraints are intentionally omitted for now.

    `max_distance` is only an isolated-conductor fallback. In the normal case,
    infinite initial directions are restricted by:
        min(finite initial extents) * scale_factor
    """

    if scale_factor < 1.0:
        raise ValueError("scale_factor must be at least 1.")
    if max_distance <= 0.0:
        raise ValueError("max_distance must be positive.")
    if touch_policy not in {"skip", "error"}:
        raise ValueError("touch_policy must be either 'skip' or 'error'.")

    others = [item for item in all_conductors if item.name != master.name]

    for other in others:
        if touches_or_overlaps(master.bounds, other.bounds):
            message = _unsupported_touch_message(master, other)
            if touch_policy == "error":
                raise UnsupportedGeometryError(message)
            print(f"WARNING: {message}")
            return None

    initial = {direction: math.inf for direction in DIRECTIONS}
    pairwise_rows: list[PairwiseDistanceRow] = []

    for other in others:
        signed = directional_distances(master.bounds, other.bounds)
        overall = block_distance(master.bounds, other.bounds)
        limiting = limiting_directions(master.bounds, other.bounds)

        pairwise_rows.append(
            PairwiseDistanceRow(
                other_conductor=other.name,
                signed_distances=signed,
                overall_distance=overall,
                limiting_directions=limiting,
            )
        )

        for direction in limiting:
            initial[direction] = min(initial[direction], overall / 2.0)

    finite_extents = [value for value in initial.values() if math.isfinite(value)]
    used_isolated_fallback = not finite_extents

    if used_isolated_fallback:
        cap_distance = max_distance
        final = {direction: max_distance for direction in DIRECTIONS}
    else:
        cap_distance = min(finite_extents) * scale_factor
        final = {
            direction: min(value, cap_distance)
            for direction, value in initial.items()
        }

    surface_bounds = master.bounds.expanded(final)
    gaussian_surface = GaussianSurface(
        master_conductor=master.name,
        bounds=surface_bounds,
        faces=make_surface_faces(surface_bounds),
    )

    return BGSGenerationResult(
        master=master,
        gaussian_surface=gaussian_surface,
        initial_extents=initial,
        final_extents=final,
        cap_distance=float(cap_distance),
        pairwise_rows=tuple(pairwise_rows),
        used_isolated_fallback=used_isolated_fallback,
    )


def generate_all_bgs(
    conductors: Iterable[Conductor],
    *,
    scale_factor: float = 1.0,
    max_distance: float = 10.0,
    touch_policy: str = "skip",
) -> list[BGSGenerationResult]:
    conductor_list = list(conductors)
    results: list[BGSGenerationResult] = []

    for master in conductor_list:
        result = generate_bgs(
            master,
            conductor_list,
            scale_factor=scale_factor,
            max_distance=max_distance,
            touch_policy=touch_policy,
        )
        if result is not None:
            results.append(result)

    return results
