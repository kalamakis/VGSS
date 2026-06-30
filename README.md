# Boundary Gaussian Surfaces, VGSS Sampling, and FRW Integration

This project provides a correctness-focused implementation of:

- conductor-level Boundary Gaussian Surface generation based on Algorithm 4.2;
- touch-connected electrical-net detection;
- net-level Virtual Gaussian Surface Set construction;
- `SampleOnVGSS` based on Algorithm 4.1;
- integration with the original geometric Floating Random Walk implementation.

The original conductor-level BGS functions and the original maximal-cube FRW helpers remain available. The VGSS functionality is also exposed as a Python API, so the project can be used either from the command line or from another Python program.

## Current scope

The implementation currently supports:

- MATLAB-style geometry files containing conductor matrices such as `C1 = [ ... ];`;
- axis-aligned cuboid conductor blocks;
- one cuboid BGS for each conductor block;
- face, edge, and corner contact as electrical connectivity;
- indirect net connectivity through intermediate touching blocks;
- rejection of overlapping conductor volumes as invalid input;
- one independent VGSS sampling context for each detected net;
- area-weighted BGS and face selection;
- geometric rejection of buried and internal interfaces;
- the `1 / n_c(r)` multiplicity correction;
- configurable importance rejection using `p(r) / U`;
- estimation of the normalization integral `H` from sampling statistics;
- 3D visualization of conductors, BGSs, VGSSs, and accepted sample points;
- use of accepted VGSS points as FRW starting points.

The default importance function is:

```text
p(r) = 1
U = 1
```

The current implementation does not model dielectric transitions or general non-Manhattan geometry. A parsed `eps_r` value is stored with the conductor but is not yet used by the VGSS sampler or FRW logic.

## Important touching-conductor rule

Electrical nets are found as connected components. Therefore, if `C1` touches `C2` and `C2` touches `C3`, all three conductors belong to the same net even when `C1` does not directly touch `C3`.

BGS generation applies a more local rule:

- a conductor directly touching the current master conductor is ignored for that master's BGS calculation;
- a same-net conductor that does not directly touch the current master is still considered;
- conductors outside the net are also considered;
- overlapping conductor volumes are rejected.

The implementation therefore ignores only the directly touching conductor or conductors, not the complete net.


## Installation

Python 3.10 or newer is required.

### Windows PowerShell

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

### Linux or macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e ".[dev]"
```

## Input geometry format

Each conductor is represented by a MATLAB-style matrix with six rows. Each row contains four 3D face vertices, so every row contains twelve numbers.

```matlab
C1 = [
    0 0 0   0 1 0   1 1 0   1 0 0;
    0 0 1   1 0 1   1 1 1   0 1 1;
    0 0 0   1 0 0   1 0 1   0 0 1;
    0 1 0   0 1 1   1 1 1   1 1 0;
    0 0 0   0 0 1   0 1 1   0 1 0;
    1 0 0   1 1 0   1 1 1   1 0 1;
];
```

MATLAB `%` comments are allowed. An `eps_r = value` declaration before a conductor matrix is also parsed and stored.

The geometry is expected to describe valid axis-aligned cuboids with unique conductor names.

# Python API

## Imports

The main BGS and VGSS functions are exported from `bgs`:

```python
from bgs import (
    VGSSSamplingStats,
    build_all_net_vgss,
    build_net_vgss,
    build_vgss_for_conductor,
    find_touching_nets,
    generate_all_bgs,
    generate_bgs,
    sample_on_vgss,
)

from bgs.matlab_parser import parse_matlab_geometry
```

The original FRW functions remain in `FRW.random_walk`:

```python
from FRW.random_walk import (
    get_system_bounds,
    run_frw_geometry,
    sample_point_on_bgs,
    sample_point_on_maximal_cube,
)
```

## Parse a geometry file

```python
from bgs.matlab_parser import parse_matlab_geometry

conductors = parse_matlab_geometry(
    "input/INPUTFILE_TOUCHING_DIRECT.m"
)

for conductor in conductors:
    print(conductor.name, conductor.min_bounds, conductor.max_bounds)
```

`parse_matlab_geometry()` returns a list of `Conductor` objects.

## Original conductor-level BGS API

### Generate one BGS

```python
from bgs import generate_bgs
from bgs.matlab_parser import parse_matlab_geometry

conductors = parse_matlab_geometry("input/INPUTFILE_05.m")
master = next(c for c in conductors if c.name == "C1")

result = generate_bgs(
    master,
    conductors,
    scale_factor=1.0,
    max_distance=10.0,
    touch_policy="skip",
)

surface = result.gaussian_surface
print(surface.bounds)
print(surface.area)
print(result.initial_extents)
print(result.final_extents)
```

`generate_bgs()` returns a `BGSGenerationResult` containing:

- `master`;
- `gaussian_surface`;
- `initial_extents`;
- `final_extents`;
- `cap_distance`;
- `pairwise_rows`;
- `used_isolated_fallback`.

`touch_policy="skip"` ignores directly touching blocks for this master's BGS. `touch_policy="error"` instead raises an error when direct contact is found.

### Generate a BGS for every conductor

```python
from bgs import generate_all_bgs

results = generate_all_bgs(
    conductors,
    scale_factor=1.0,
    max_distance=10.0,
    touch_policy="skip",
)

for result in results:
    print(result.master.name, result.gaussian_surface.area)
```

These functions are retained for code that needs only the original conductor-level Algorithm 4.2 behavior.

## Detect electrical nets

```python
from bgs import find_touching_nets

nets = find_touching_nets(conductors)

for net in nets:
    print(net.name, net.conductor_names)
```

For `INPUTFILE_TOUCHING_DIRECT.m`, the expected nets are:

```text
Net1: C1, C2, C3
Net2: C4
Net3: C5
```

## Build the VGSS for a selected conductor's net

`build_vgss_for_conductor()` is the simplest entry point when a conductor name is known.

```python
from bgs import build_vgss_for_conductor

net_vgss = build_vgss_for_conductor(
    conductors,
    "C1",
    scale_factor=1.0,
    max_distance=10.0,
)

print(net_vgss.net.name)
print(net_vgss.net.conductor_names)
print(len(net_vgss.surfaces))
```

The returned `NetVGSS` contains:

- `net`: the detected `ConductorNet`;
- `bgs_results`: one `BGSGenerationResult` per conductor in the net;
- `sampling_context`: precomputed Algorithm 4.1 data;
- `surfaces`: a convenience property returning the net's BGS objects.

## Build the VGSS for an existing net

```python
from bgs import build_net_vgss, find_touching_nets

nets = find_touching_nets(conductors)
selected_net = nets[0]

net_vgss = build_net_vgss(
    selected_net,
    conductors,
    scale_factor=1.0,
    max_distance=10.0,
)
```

Use this form when net detection and net selection are handled separately.

## Build every net-level VGSS

```python
from bgs import build_all_net_vgss

all_net_vgss = build_all_net_vgss(
    conductors,
    scale_factor=1.0,
    max_distance=10.0,
)

for item in all_net_vgss:
    print(item.net.name, item.net.conductor_names)
```

`build_all_net_vgss()` returns a tuple containing one independent `NetVGSS` object for each detected net.

## Sample one accepted VGSS point

```python
import numpy as np

from bgs import build_vgss_for_conductor, sample_on_vgss

net_vgss = build_vgss_for_conductor(conductors, "C1")
rng = np.random.default_rng(1234)

r = sample_on_vgss(net_vgss.sampling_context, rng)
print(r)
```

`sample_on_vgss()` returns only the accepted coordinate:

```text
[x, y, z]
```

The returned value is a NumPy array with shape `(3,)`.

A different point is proposed for every call. Reuse the same NumPy generator when deterministic repeatability is required.

## Sample multiple points from every net

```python
import numpy as np

from bgs import build_all_net_vgss, sample_on_vgss

rng = np.random.default_rng(1234)
all_net_vgss = build_all_net_vgss(conductors)

sampled_points = {
    item.net.name: np.vstack(
        [
            sample_on_vgss(item.sampling_context, rng)
            for _ in range(200)
        ]
    )
    for item in all_net_vgss
}
```

## Custom importance function `p(r)`

The importance function and its upper bound are attached to the sampling context when the VGSS is built.

```python
import numpy as np

from bgs import build_vgss_for_conductor, sample_on_vgss


def F(r: np.ndarray) -> float:
    return 0.5


net_vgss = build_vgss_for_conductor(
    conductors,
    "C1",
    importance_function=F,
    upper_bound=1.0,
)

rng = np.random.default_rng(1234)
r = sample_on_vgss(net_vgss.sampling_context, rng)
```

The caller must currently ensure that:

```text
U > 0
0 <= p(r) <= U
```

for every possible VGSS point. An invalid `p(r)` or `U` can make the rejection sampler incorrect or prevent acceptance.

## Estimate `H`

`VGSSSamplingStats` records raw proposals and all rejection categories.

```python
import numpy as np

from bgs import VGSSSamplingStats, sample_on_vgss

rng = np.random.default_rng(1234)
stats = VGSSSamplingStats()

points = np.vstack(
    [
        sample_on_vgss(
            net_vgss.sampling_context,
            rng,
            stats=stats,
        )
        for _ in range(5000)
    ]
)

H = stats.estimate_H(net_vgss.sampling_context)
print(H)
print(stats.as_dict(net_vgss.sampling_context))
```

The estimator is:

```text
H = U * A_raw * accepted_count / proposal_count
```

where `A_raw` is the sum of the areas of the component BGSs stored in the sampling context.

For `p(r) = 1`, `H` estimates the actual exterior VGSS area after the geometry and multiplicity corrections.

## Visualize VGSS results

```python
from bgs import plot_vgss_results

plot_vgss_results(
    conductors,
    all_net_vgss,
    sampled_points,
    save_path="output/all_net_vgss_samples.png",
    show=False,
)
```

The `sampled_points` dictionary must be keyed by net name, for example `Net1`.

# FRW integration

The FRW implementation keeps its original maximal-cube walk logic. The integration changes only the source of the initial point: every walk begins from a fresh point accepted by `SampleOnVGSS`.

## Run FRW for one selected net

```python
import numpy as np

from FRW.random_walk import run_frw_geometry
from bgs import build_vgss_for_conductor
from bgs.matlab_parser import parse_matlab_geometry

conductors = parse_matlab_geometry(
    "input/INPUTFILE_TOUCHING_DIRECT.m"
)

master_vgss = build_vgss_for_conductor(
    conductors,
    "C1",
    scale_factor=1.25,
    max_distance=10.0,
)

result = run_frw_geometry(
    conductors,
    master_vgss,
    np.random.default_rng(1234),
    num_walks=5000,
    max_hops=100,
)

print(result["H"])
print(result["sampling_stats"])
```

## Run FRW for every detected net

```python
import numpy as np

from FRW.random_walk import run_frw_geometry
from bgs import build_all_net_vgss

rng = np.random.default_rng(1234)
all_net_vgss = build_all_net_vgss(conductors)

results = {
    item.net.name: run_frw_geometry(
        conductors,
        item,
        rng,
        num_walks=5000,
        max_hops=100,
    )
    for item in all_net_vgss
}
```

## FRW return value

`run_frw_geometry()` returns:

```python
{
    "H": H_estimate,
    "sampling_stats": {
        "proposal_count": ...,
        "accepted_count": ...,
        "rejection_count": ...,
        "geometry_rejections": ...,
        "multiplicity_rejections": ...,
        "importance_rejections": ...,
        "acceptance_rate": ...,
        "upper_bound_U": ...,
        "total_component_area": ...,
        "H_estimate": ...,
    },
    "walks": [
        {
            "start_point": [x, y, z],
            "path_data": [
                {
                    "center": [x, y, z],
                    "a": maximal_cube_side_length,
                }
            ],
            "hit_conductor": conductor_name_or_ground,
        }
    ],
}
```

The existing `path_data` and `hit_conductor` fields are preserved. `start_point` and the VGSS sampling statistics are added by the integration.

# Command-line usage

The module commands below work directly with the current source tree after installation.

## Generate one conductor-level BGS

```bash
python -m bgs.main input/INPUTFILE_05.m \
    --master C1 \
    --scale-factor 2
```

Save the plot without opening a window:

```bash
python -m bgs.main input/INPUTFILE_05.m \
    --master C1 \
    --scale-factor 2 \
    --save-plot output/C1_bgs.png \
    --no-show
```

## Generate BGSs for every conductor

```bash
python -m bgs.main input/INPUTFILE_05.m \
    --all \
    --scale-factor 2 \
    --save-plot output/all_bgs.png \
    --no-show
```

When `--save-plot` is omitted in `--all` mode, the combined plot is saved as `output/all_bgs.png`.

## Sample one selected net

`--net-master` identifies a conductor belonging to the desired net.

```bash
python -m bgs.vgss_cli input/INPUTFILE_TOUCHING_DIRECT.m \
    --net-master C1 \
    --count 10 \
    --seed 1234 \
    --no-show
```

Save coordinates and a visualization:

```bash
python -m bgs.vgss_cli input/INPUTFILE_TOUCHING_DIRECT.m \
    --net-master C1 \
    --count 1000 \
    --seed 1234 \
    --save-points output/vgss_points.csv \
    --save-plot output/net1_vgss.png \
    --no-show
```

Single-net CSV output contains:

```text
x,y,z
```

## Sample every detected net

```bash
python -m bgs.vgss_cli input/INPUTFILE_TOUCHING_DIRECT.m \
    --all-nets \
    --count 1000 \
    --seed 1234 \
    --save-points output/all_net_vgss_points.csv \
    --save-plot output/all_net_vgss_samples.png \
    --no-show
```

With `--all-nets`, `--count` is the number of accepted points generated for each net. The CSV contains:

```text
net,x,y,z
```

The installed `vgss-sample` console command is equivalent to `python -m bgs.vgss_cli`.

## Run the integrated FRW

```bash
python -m FRW.cli input/INPUTFILE_TOUCHING_DIRECT.m \
    --scale-factor 1.25 \
    --max-distance 10 \
    --walks 5000 \
    --seed 1234 \
    --output output/frw_exported_data.json \
    --no-visualization
```

The FRW command-line interface currently selects the first detected net. Use the Python API when a different net or every net must be processed.

# Parameters

## `scale_factor`

Must be at least `1.0`.

For a non-isolated conductor, the BGS cap is calculated as:

```text
min(finite initial extents) * scale_factor
```

Each final directional extent is limited by that cap.

## `max_distance`

Must be positive.

It is used as a fallback extent only when no finite non-touching conductor constraint exists for the current master conductor.

## `abs_tol`

Controls floating-point comparisons for touching, overlap, surface coincidence, and candidate classification. The default is `1e-12`.

## `max_attempts`

`sample_on_vgss()` defaults to `10000` proposal attempts for one accepted point. It raises `RuntimeError` when no proposal is accepted within that limit.

# Tests

Run the complete test suite from the repository root:

```bash
pytest
```

The current suite covers:

- directional distances;
- BGS generation;
- parser behavior;
- direct-touch skipping;
- overlap rejection;
- transitive net construction;
- Algorithm 4.1 geometry rejection;
- multiplicity rejection;
- all-net VGSS construction;
- VGSS visualization;
- `H` estimation;
- FRW integration and output compatibility.

# Current limitations

- Conductors must be axis-aligned cuboids.
- Overlapping conductor volumes are invalid input.
- Dielectric transitions are not implemented.
- Parsed relative permittivity is not yet used by the sampler.
- The caller must currently provide a valid positive `U` and a function satisfying `0 <= p(r) <= U`.
- The FRW command-line interface processes only the first detected net.
- The implementation prioritizes correctness and clarity over large-scale performance optimization.
