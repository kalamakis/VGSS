from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import TYPE_CHECKING

import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

from .models import Bounds, Conductor, GaussianSurface, make_surface_faces

if TYPE_CHECKING:
    from .vgss import NetVGSS


def _add_box_faces(
    ax,
    bounds: Bounds,
    *,
    alpha: float,
    linewidth: float,
    linestyle: str = "-",
    facecolor=None,
    edgecolor=None,
) -> None:
    faces = [face.vertices for face in make_surface_faces(bounds)]
    collection = Poly3DCollection(
        faces,
        alpha=alpha,
        linewidths=linewidth,
        linestyles=linestyle,
        facecolors=facecolor,
        edgecolors=edgecolor,
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


def _validate_points(points: np.ndarray, net_name: str) -> np.ndarray:
    point_array = np.asarray(points, dtype=float)
    if point_array.size == 0:
        return np.empty((0, 3), dtype=float)
    if point_array.ndim == 1:
        point_array = point_array.reshape(1, -1)
    if point_array.ndim != 2 or point_array.shape[1] != 3:
        raise ValueError(
            f"Sample points for {net_name} must have shape (N, 3)."
        )
    if not np.all(np.isfinite(point_array)):
        raise ValueError(f"Sample points for {net_name} must be finite.")
    return point_array


def plot_geometry(
    conductors: Iterable[Conductor],
    *,
    selected_surface: GaussianSurface | None = None,
    selected_surfaces: Iterable[GaussianSurface] | None = None,
    save_path: str | Path | None = None,
    show: bool = True,
) -> None:
    conductor_list = list(conductors)
    if not conductor_list:
        raise ValueError("At least one conductor is required for plotting.")

    if selected_surface is not None and selected_surfaces is not None:
        raise ValueError(
            "Pass either selected_surface or selected_surfaces, not both."
        )

    surface_list = (
        list(selected_surfaces)
        if selected_surfaces is not None
        else ([selected_surface] if selected_surface is not None else [])
    )
    master_names = {surface.master_conductor for surface in surface_list}

    figure = plt.figure(figsize=(10, 7))
    ax = figure.add_subplot(111, projection="3d")

    for conductor in conductor_list:
        is_master = conductor.name in master_names
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

    for surface in surface_list:
        _add_box_faces(
            ax,
            surface.bounds,
            alpha=0.08,
            linewidth=1.8,
            linestyle="--",
        )
        all_bounds.append(surface.bounds)

    if len(surface_list) == 1:
        ax.set_title(
            f"Conductors and BGS for {surface_list[0].master_conductor}"
        )
    elif surface_list:
        ax.set_title("Conductors and all generated BGSs")
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


def plot_vgss_results(
    conductors: Iterable[Conductor],
    net_vgss_collection: Sequence[NetVGSS],
    sampled_points: Mapping[str, np.ndarray],
    *,
    save_path: str | Path | None = None,
    show: bool = True,
) -> None:
    """
    Plot circuit conductors, every selected net's BGSs, and accepted VGSS points.

    `sampled_points` is keyed by `ConductorNet.name`, for example `Net1`.
    The BGSs and accepted points belonging to the same net share one color.
    """

    conductor_list = list(conductors)
    net_vgss_list = list(net_vgss_collection)

    if not conductor_list:
        raise ValueError("At least one conductor is required for plotting.")
    if not net_vgss_list:
        raise ValueError("At least one net-level VGSS is required for plotting.")

    known_net_names = {net_vgss.net.name for net_vgss in net_vgss_list}
    unknown_names = set(sampled_points) - known_net_names
    if unknown_names:
        names = ", ".join(sorted(unknown_names))
        raise ValueError(f"Sample points were supplied for unknown nets: {names}.")

    figure = plt.figure(figsize=(11, 8))
    ax = figure.add_subplot(111, projection="3d")

    # Conductors are the physical geometry; keep them neutral so the net colors
    # remain dedicated to BGS outlines and accepted sample points.
    for conductor in conductor_list:
        _add_box_faces(
            ax,
            conductor.bounds,
            alpha=0.20,
            linewidth=0.9,
            facecolor="0.75",
            edgecolor="0.25",
        )
        center = np.array(
            [
                (conductor.bounds.xmin + conductor.bounds.xmax) / 2,
                (conductor.bounds.ymin + conductor.bounds.ymax) / 2,
                (conductor.bounds.zmin + conductor.bounds.zmax) / 2,
            ]
        )
        ax.text(*center, conductor.name, fontsize=8)

    all_bounds = [conductor.bounds for conductor in conductor_list]
    default_colors = plt.rcParams["axes.prop_cycle"].by_key().get("color", [])
    legend_handles: list[Line2D] = []

    for index, net_vgss in enumerate(net_vgss_list):
        color = default_colors[index % len(default_colors)] if default_colors else None

        for surface in net_vgss.surfaces:
            _add_box_faces(
                ax,
                surface.bounds,
                alpha=0.035,
                linewidth=1.6,
                linestyle="--",
                facecolor=color,
                edgecolor=color,
            )
            all_bounds.append(surface.bounds)

        points = _validate_points(
            sampled_points.get(net_vgss.net.name, np.empty((0, 3))),
            net_vgss.net.name,
        )
        if len(points):
            ax.scatter(
                points[:, 0],
                points[:, 1],
                points[:, 2],
                s=12,
                alpha=0.82,
                color=color,
                depthshade=False,
            )

        conductor_names = ", ".join(net_vgss.net.conductor_names)
        legend_handles.append(
            Line2D(
                [0],
                [0],
                marker="o",
                linestyle="--",
                color=color,
                markersize=5,
                label=(
                    f"{net_vgss.net.name}: {conductor_names} "
                    f"({len(points)} samples)"
                ),
            )
        )

    ax.set_title(
        "VGSS accepted samples for all detected nets"
        if len(net_vgss_list) > 1
        else f"VGSS accepted samples for {net_vgss_list[0].net.name}"
    )
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_zlabel("Z")
    _set_equal_axes(ax, all_bounds)
    ax.legend(handles=legend_handles, loc="upper left", fontsize=8)
    figure.tight_layout()

    if save_path is not None:
        print(f"Saving VGSS plot to {save_path}...")
        output_path = Path(save_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output_path, dpi=180, bbox_inches="tight")

    if show:
        plt.show()
    else:
        plt.close(figure)
