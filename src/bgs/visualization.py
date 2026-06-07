from __future__ import annotations

from collections.abc import Iterable
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from .models import Bounds, Conductor, GaussianSurface, make_surface_faces


def _add_box_faces(
    ax,
    bounds: Bounds,
    *,
    alpha: float,
    linewidth: float,
    linestyle: str = "-",
) -> None:
    faces = [face.vertices for face in make_surface_faces(bounds)]
    collection = Poly3DCollection(
        faces,
        alpha=alpha,
        linewidths=linewidth,
        linestyles=linestyle,
    )
    ax.add_collection3d(collection)


def _set_equal_axes(ax, all_bounds: list[Bounds]) -> None:
    xmin = min(bounds.xmin for bounds in all_bounds)
    xmax = max(bounds.xmax for bounds in all_bounds)
    ymin = min(bounds.ymin for bounds in all_bounds)
    ymax = max(bounds.ymax for bounds in all_bounds)
    zmin = min(bounds.zmin for bounds in all_bounds)
    zmax = max(bounds.zmax for bounds in all_bounds)

    xmid, ymid, zmid = (xmin + xmax) / 2, (ymin + ymax) / 2, (zmin + zmax) / 2
    radius = max(xmax - xmin, ymax - ymin, zmax - zmin) / 2
    radius = max(radius, 0.5)

    ax.set_xlim(xmid - radius, xmid + radius)
    ax.set_ylim(ymid - radius, ymid + radius)
    ax.set_zlim(zmid - radius, zmid + radius)


def plot_geometry(
    conductors: Iterable[Conductor],
    *,
    selected_surface: GaussianSurface | None = None,
    save_path: str | Path | None = None,
    show: bool = True,
) -> None:
    conductor_list = list(conductors)
    if not conductor_list:
        raise ValueError("At least one conductor is required for plotting.")

    figure = plt.figure(figsize=(10, 7))
    ax = figure.add_subplot(111, projection="3d")

    for conductor in conductor_list:
        is_master = (
            selected_surface is not None
            and conductor.name == selected_surface.master_conductor
        )
        _add_box_faces(
            ax,
            conductor.bounds,
            alpha=0.48 if is_master else 0.26,
            linewidth=2.0 if is_master else 0.9,
        )
        center = np.array(
            [
                (conductor.bounds.xmin + conductor.bounds.xmax) / 2,
                (conductor.bounds.ymin + conductor.bounds.ymax) / 2,
                (conductor.bounds.zmin + conductor.bounds.zmax) / 2,
            ]
        )
        ax.text(*center, conductor.name)

    all_bounds = [conductor.bounds for conductor in conductor_list]

    if selected_surface is not None:
        _add_box_faces(
            ax,
            selected_surface.bounds,
            alpha=0.08,
            linewidth=1.8,
            linestyle="--",
        )
        all_bounds.append(selected_surface.bounds)
        ax.set_title(
            f"Conductors and BGS for {selected_surface.master_conductor}"
        )
    else:
        ax.set_title("Conductors")

    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    _set_equal_axes(ax, all_bounds)
    figure.tight_layout()

    if save_path is not None:
        print(f"Saving plot to {save_path}...")
        output_path = Path(save_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output_path, dpi=180, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close(figure)
