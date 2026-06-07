from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import numpy as np

DIRECTIONS = ("PX", "PY", "PZ", "NX", "NY", "NZ")


@dataclass(frozen=True)
class Bounds:
    """Axis-aligned bounds for a cuboid."""

    xmin: float
    xmax: float
    ymin: float
    ymax: float
    zmin: float
    zmax: float

    def __post_init__(self) -> None:
        if not self.xmin < self.xmax:
            raise ValueError("Expected xmin < xmax.")
        if not self.ymin < self.ymax:
            raise ValueError("Expected ymin < ymax.")
        if not self.zmin < self.zmax:
            raise ValueError("Expected zmin < zmax.")

    @classmethod
    def from_vertices(cls, vertices: np.ndarray) -> "Bounds":
        points = np.asarray(vertices, dtype=float).reshape(-1, 3)
        return cls(
            xmin=float(points[:, 0].min()),
            xmax=float(points[:, 0].max()),
            ymin=float(points[:, 1].min()),
            ymax=float(points[:, 1].max()),
            zmin=float(points[:, 2].min()),
            zmax=float(points[:, 2].max()),
        )

    def expanded(self, extents: dict[str, float]) -> "Bounds":
        return Bounds(
            xmin=self.xmin - extents["NX"],
            xmax=self.xmax + extents["PX"],
            ymin=self.ymin - extents["NY"],
            ymax=self.ymax + extents["PY"],
            zmin=self.zmin - extents["NZ"],
            zmax=self.zmax + extents["PZ"],
        )

    def vertices(self) -> np.ndarray:
        return np.array(
            [
                [self.xmin, self.ymin, self.zmin],
                [self.xmax, self.ymin, self.zmin],
                [self.xmax, self.ymax, self.zmin],
                [self.xmin, self.ymax, self.zmin],
                [self.xmin, self.ymin, self.zmax],
                [self.xmax, self.ymin, self.zmax],
                [self.xmax, self.ymax, self.zmax],
                [self.xmin, self.ymax, self.zmax],
            ],
            dtype=float,
        )


@dataclass(frozen=True)
class Conductor:
    """A conductor block parsed from the input geometry."""

    name: str
    bounds: Bounds
    face_vertices: np.ndarray
    relative_permittivity: float | None = None


@dataclass(frozen=True)
class SurfaceFace:
    """One rectangular face of a generated cuboid BGS."""

    direction: str
    vertices: np.ndarray
    normal: np.ndarray
    area: float


@dataclass(frozen=True)
class GaussianSurface:
    """Cuboid Boundary Gaussian Surface enclosing one master conductor."""

    master_conductor: str
    bounds: Bounds
    faces: tuple[SurfaceFace, ...]

    @property
    def area(self) -> float:
        return float(sum(face.area for face in self.faces))


def make_surface_faces(bounds: Bounds) -> tuple[SurfaceFace, ...]:
    """Construct the six outward-facing rectangles of a cuboid."""

    x0, x1 = bounds.xmin, bounds.xmax
    y0, y1 = bounds.ymin, bounds.ymax
    z0, z1 = bounds.zmin, bounds.zmax

    raw_faces = {
        "NX": (
            [[x0, y0, z0], [x0, y0, z1], [x0, y1, z1], [x0, y1, z0]],
            [-1.0, 0.0, 0.0],
            (y1 - y0) * (z1 - z0),
        ),
        "PX": (
            [[x1, y0, z0], [x1, y1, z0], [x1, y1, z1], [x1, y0, z1]],
            [1.0, 0.0, 0.0],
            (y1 - y0) * (z1 - z0),
        ),
        "NY": (
            [[x0, y0, z0], [x1, y0, z0], [x1, y0, z1], [x0, y0, z1]],
            [0.0, -1.0, 0.0],
            (x1 - x0) * (z1 - z0),
        ),
        "PY": (
            [[x0, y1, z0], [x0, y1, z1], [x1, y1, z1], [x1, y1, z0]],
            [0.0, 1.0, 0.0],
            (x1 - x0) * (z1 - z0),
        ),
        "NZ": (
            [[x0, y0, z0], [x0, y1, z0], [x1, y1, z0], [x1, y0, z0]],
            [0.0, 0.0, -1.0],
            (x1 - x0) * (y1 - y0),
        ),
        "PZ": (
            [[x0, y0, z1], [x1, y0, z1], [x1, y1, z1], [x0, y1, z1]],
            [0.0, 0.0, 1.0],
            (x1 - x0) * (y1 - y0),
        ),
    }

    return tuple(
        SurfaceFace(
            direction=direction,
            vertices=np.asarray(raw_faces[direction][0], dtype=float),
            normal=np.asarray(raw_faces[direction][1], dtype=float),
            area=float(raw_faces[direction][2]),
        )
        for direction in DIRECTIONS
    )
