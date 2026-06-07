# Boundary Gaussian Surface generator

This first milestone implements the conductor-only part of Algorithm 4.2 for
axis-aligned cuboid conductor blocks.

It reads MATLAB-style geometry files containing matrices such as:

```matlab
C1 = [
    ...
];
```

Each row represents one rectangular face using four 3D vertices.

## Current scope

- Parse conductor blocks from `.m` input files.
- Extract axis-aligned bounding boxes.
- Calculate the six signed directional distances:
  `PX`, `PY`, `PZ`, `NX`, `NY`, `NZ`.
- Generate a cuboid Boundary Gaussian Surface (BGS) around one conductor or all
  conductors.
- Print intermediate distance tables in the terminal.
- Display or save a 3D plot.
- Detect touching or overlapping blocks and skip them by default because
  multi-block conductor merging is intentionally reserved for a later milestone.

Dielectric transitions are intentionally not implemented yet.

The code already stores each BGS as six faces with vertices, normals, and areas.
That representation is intended for the later implementation of
`SampleOnVGSS`.

## Setup

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -e ".[dev]"
```

### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e ".[dev]"
```

## Run the demo

Generate the BGS for `C1`, use a scale factor of `2`, print the calculations,
and save the plot:

```bash
bgs-generate input/INPUTFILE_05.m ^
    --master C1 ^
    --scale-factor 2 ^
    --save-plot output/C1_bgs.png
```

On Linux or macOS, replace `^` with `\`.

To avoid opening an interactive window:

```bash
bgs-generate input/INPUTFILE_05.m --master C1 --scale-factor 2 \
    --save-plot output/C1_bgs.png --no-show
```

Generate surfaces for every supported conductor:

```bash
bgs-generate input/INPUTFILE_05.m --all --scale-factor 2
```

## About `max_distance`

Algorithm 4.2 normally does not need a hard maximum distance. Directions with no
nearby conductor initially remain infinite and are later restricted by:

```text
minimum finite extent * scale_factor
```

The CLI option `--max-distance` is only a fallback for an isolated conductor,
where all six initial distances remain infinite.

## Touching conductors

The current implementation treats touching and overlapping blocks as an
unsupported geometry case. With the default policy, affected BGS generation is
skipped and a warning is printed:

```bash
bgs-generate input/file.m --touch-policy skip
```

For strict validation:

```bash
bgs-generate input/file.m --touch-policy error
```

A future extension can merge touching blocks that belong to the same physical
conductor.

## Tests

```bash
pytest
```

## Later milestone: `SampleOnVGSS`

The package includes a placeholder module named `sampling.py`. The generated
BGS objects already expose face areas, vertices, and outward normals. These are
the geometric building blocks needed for area-weighted BGS sampling and uniform
surface-point sampling.
