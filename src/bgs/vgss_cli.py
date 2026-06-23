from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np

from .matlab_parser import parse_matlab_geometry
from .sampling import sample_on_vgss
from .topology import find_touching_nets
from .vgss import build_all_net_vgss, build_vgss_for_conductor
from .visualization import plot_vgss_results


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Detect touch-connected conductor nets, build net-level VGSS "
            "contexts, sample points with Algorithm 4.1, and visualize them."
        )
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the MATLAB-style geometry input file.",
    )

    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument(
        "--net-master",
        help=(
            "A conductor name identifying one net, for example C1. Every "
            "face/edge/corner-connected block in its component is included."
        ),
    )
    selection.add_argument(
        "--all-nets",
        action="store_true",
        help="Build and sample one independent VGSS for every detected net.",
    )

    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help=(
            "Number of accepted points per selected net. "
            "Default: 1."
        ),
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=None,
        help="Optional NumPy random seed for reproducible sampling.",
    )
    parser.add_argument(
        "--scale-factor",
        type=float,
        default=1.0,
        help="Algorithm 4.2 scale factor. Default: 1.",
    )
    parser.add_argument(
        "--max-distance",
        type=float,
        default=10.0,
        help="Fallback extent for an isolated BGS. Default: 10.",
    )
    parser.add_argument(
        "--abs-tol",
        type=float,
        default=1e-12,
        help="Absolute geometric tolerance. Default: 1e-12.",
    )
    parser.add_argument(
        "--save-points",
        type=Path,
        default=None,
        help=(
            "Optional CSV output path. All-net output includes a net column."
        ),
    )
    parser.add_argument(
        "--save-plot",
        type=Path,
        default=None,
        help="Optional path for saving the 3D VGSS visualization.",
    )
    parser.add_argument(
        "--no-show",
        action="store_true",
        help="Do not open the interactive 3D plot window.",
    )
    return parser


def _sample_points(net_vgss, count: int, rng: np.random.Generator) -> np.ndarray:
    return np.vstack(
        [
            sample_on_vgss(net_vgss.sampling_context, rng)
            for _ in range(count)
        ]
    )


def _save_points_csv(
    output_path: Path,
    sampled_points: dict[str, np.ndarray],
    *,
    include_net_column: bool,
) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["net", "x", "y", "z"] if include_net_column else ["x", "y", "z"])
        for net_name, points in sampled_points.items():
            for point in points:
                row = [net_name, *point] if include_net_column else list(point)
                writer.writerow(row)


def main() -> None:
    args = _build_parser().parse_args()
    if args.count <= 0:
        raise SystemExit("--count must be positive.")

    conductors = parse_matlab_geometry(args.input_file)
    nets = find_touching_nets(conductors, abs_tol=args.abs_tol)

    print("Detected nets:")
    for net in nets:
        marker = (
            " *"
            if args.net_master is not None
            and args.net_master in net.conductor_names
            else ""
        )
        print(f"  {net.name}: {', '.join(net.conductor_names)}{marker}")

    if args.all_nets:
        net_vgss_collection = build_all_net_vgss(
            conductors,
            scale_factor=args.scale_factor,
            max_distance=args.max_distance,
            abs_tol=args.abs_tol,
        )
    else:
        try:
            selected = build_vgss_for_conductor(
                conductors,
                args.net_master,
                scale_factor=args.scale_factor,
                max_distance=args.max_distance,
                abs_tol=args.abs_tol,
            )
        except KeyError as exc:
            raise SystemExit(str(exc)) from exc
        net_vgss_collection = (selected,)

    rng = np.random.default_rng(args.seed)
    sampled_points = {
        net_vgss.net.name: _sample_points(net_vgss, args.count, rng)
        for net_vgss in net_vgss_collection
    }

    print()
    for net_vgss in net_vgss_collection:
        points = sampled_points[net_vgss.net.name]
        print(
            f"Sampled {len(points)} point(s) from {net_vgss.net.name} "
            f"({', '.join(net_vgss.net.conductor_names)}) using "
            f"{len(net_vgss.surfaces)} BGS(s), p(r)=1, U=1:"
        )
        for point in points:
            print(f"  {point[0]:.12g} {point[1]:.12g} {point[2]:.12g}")
        print()

    if args.save_points is not None:
        _save_points_csv(
            args.save_points,
            sampled_points,
            include_net_column=args.all_nets,
        )
        print(f"Saved points to {args.save_points}")

    plot_vgss_results(
        conductors,
        net_vgss_collection,
        sampled_points,
        save_path=args.save_plot,
        show=not args.no_show,
    )


if __name__ == "__main__":
    main()
