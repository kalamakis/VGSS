from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from .matlab_parser import parse_matlab_geometry
from .sampling import sample_on_vgss
from .topology import find_touching_nets
from .vgss import build_vgss_for_conductor


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Detect touch-connected conductor nets, build one net-level VGSS, "
            "and sample points with Algorithm 4.1."
        )
    )
    parser.add_argument(
        "input_file",
        type=Path,
        help="Path to the MATLAB-style geometry input file.",
    )
    parser.add_argument(
        "--net-master",
        required=True,
        help=(
            "A conductor name identifying the net to sample, for example C1. "
            "Every face/edge/corner-connected block in its component is included."
        ),
    )
    parser.add_argument(
        "--count",
        type=int,
        default=1,
        help="Number of accepted VGSS points to generate. Default: 1.",
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
        help="Optional CSV output path for the accepted points.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()
    if args.count <= 0:
        raise SystemExit("--count must be positive.")

    conductors = parse_matlab_geometry(args.input_file)
    nets = find_touching_nets(conductors, abs_tol=args.abs_tol)

    print("Detected nets:")
    for net in nets:
        marker = " *" if args.net_master in net.conductor_names else ""
        print(f"  {net.name}: {', '.join(net.conductor_names)}{marker}")

    try:
        net_vgss = build_vgss_for_conductor(
            conductors,
            args.net_master,
            scale_factor=args.scale_factor,
            max_distance=args.max_distance,
            abs_tol=args.abs_tol,
        )
    except KeyError as exc:
        raise SystemExit(str(exc)) from exc

    rng = np.random.default_rng(args.seed)
    points = np.vstack(
        [
            sample_on_vgss(net_vgss.sampling_context, rng)
            for _ in range(args.count)
        ]
    )

    print()
    print(
        f"Sampled {len(points)} point(s) from {net_vgss.net.name} "
        f"using {len(net_vgss.surfaces)} BGS(s), p(r)=1, U=1:"
    )
    for point in points:
        print(f"  {point[0]:.12g} {point[1]:.12g} {point[2]:.12g}")

    if args.save_points is not None:
        args.save_points.parent.mkdir(parents=True, exist_ok=True)
        np.savetxt(
            args.save_points,
            points,
            delimiter=",",
            header="x,y,z",
            comments="",
        )
        print(f"Saved points to {args.save_points}")


if __name__ == "__main__":
    main()
