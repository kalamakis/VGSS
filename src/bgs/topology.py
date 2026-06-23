from __future__ import annotations

from collections import deque
from collections.abc import Sequence
from dataclasses import dataclass

from .distances import boxes_overlap, boxes_touch
from .models import Conductor


class InvalidConductorGeometryError(ValueError):
    """Raised when the input conductor geometry is not valid for this project."""


@dataclass(frozen=True)
class ConductorNet:
    """One electrical net represented by a touch-connected conductor component."""

    index: int
    conductors: tuple[Conductor, ...]

    @property
    def name(self) -> str:
        return f"Net{self.index}"

    @property
    def conductor_names(self) -> tuple[str, ...]:
        return tuple(conductor.name for conductor in self.conductors)


def find_touching_nets(
    conductors: Sequence[Conductor],
    *,
    abs_tol: float = 1e-12,
) -> tuple[ConductorNet, ...]:
    """
    Group conductor blocks into electrical nets using geometric contact.

    Face, edge, and corner contact all create graph edges.  Nets are the
    connected components of that graph, so contact may be indirect through
    intermediate blocks.

    Overlapping conductor volumes are rejected as invalid input.
    """

    conductor_list = list(conductors)
    if not conductor_list:
        return ()

    names = [conductor.name for conductor in conductor_list]
    if len(set(names)) != len(names):
        raise InvalidConductorGeometryError(
            "Conductor names must be unique before nets can be constructed."
        )

    adjacency: list[list[int]] = [[] for _ in conductor_list]

    for first_index, first in enumerate(conductor_list):
        for second_index in range(first_index + 1, len(conductor_list)):
            second = conductor_list[second_index]

            if boxes_overlap(first.bounds, second.bounds, abs_tol=abs_tol):
                raise InvalidConductorGeometryError(
                    f"{first.name} and {second.name} overlap. "
                    "Overlapping conductor blocks are invalid input."
                )

            if boxes_touch(first.bounds, second.bounds, abs_tol=abs_tol):
                adjacency[first_index].append(second_index)
                adjacency[second_index].append(first_index)

    visited = [False] * len(conductor_list)
    nets: list[ConductorNet] = []

    for start_index in range(len(conductor_list)):
        if visited[start_index]:
            continue

        queue: deque[int] = deque([start_index])
        visited[start_index] = True
        component_indices: list[int] = []

        while queue:
            current_index = queue.popleft()
            component_indices.append(current_index)

            for neighbor_index in adjacency[current_index]:
                if not visited[neighbor_index]:
                    visited[neighbor_index] = True
                    queue.append(neighbor_index)

        component_indices.sort()
        nets.append(
            ConductorNet(
                index=len(nets) + 1,
                conductors=tuple(
                    conductor_list[index] for index in component_indices
                ),
            )
        )

    return tuple(nets)


def find_net_containing(
    nets: Sequence[ConductorNet],
    conductor_name: str,
) -> ConductorNet:
    """Return the net containing the named conductor."""

    for net in nets:
        if conductor_name in net.conductor_names:
            return net

    available = ", ".join(
        conductor_name
        for net in nets
        for conductor_name in net.conductor_names
    )
    raise KeyError(
        f"Unknown conductor {conductor_name!r}. "
        f"Available conductors: {available}"
    )
