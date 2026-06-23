from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from .gaussian_surface import BGSGenerationResult, generate_bgs
from .models import Conductor, GaussianSurface
from .sampling import (
    ImportanceFunction,
    VGSSSamplingContext,
    prepare_vgss_sampling,
    uniform_importance,
)
from .topology import ConductorNet, find_net_containing, find_touching_nets


@dataclass(frozen=True)
class NetVGSS:
    """The BGS collection and sampling context for one touch-connected net."""

    net: ConductorNet
    bgs_results: tuple[BGSGenerationResult, ...]
    sampling_context: VGSSSamplingContext

    @property
    def surfaces(self) -> tuple[GaussianSurface, ...]:
        return tuple(
            result.gaussian_surface
            for result in self.bgs_results
        )


def build_net_vgss(
    net: ConductorNet,
    all_conductors: Sequence[Conductor],
    *,
    scale_factor: float = 1.0,
    max_distance: float = 10.0,
    importance_function: ImportanceFunction = uniform_importance,
    upper_bound: float = 1.0,
    abs_tol: float = 1e-12,
) -> NetVGSS:
    """
    Generate the individual BGSs and prepare Algorithm 4.1 for one net.

    Each block BGS is still constrained by every non-touching conductor in the
    complete circuit.  Directly touching blocks are ignored only for that block's
    Algorithm 4.2 construction, as required by the current project rules.
    """

    conductor_list = list(all_conductors)
    bgs_results: list[BGSGenerationResult] = []

    for master in net.conductors:
        result = generate_bgs(
            master,
            conductor_list,
            scale_factor=scale_factor,
            max_distance=max_distance,
            touch_policy="skip",
        )
        if result is None:
            raise RuntimeError(
                f"BGS generation unexpectedly skipped conductor {master.name}."
            )
        bgs_results.append(result)

    surfaces = tuple(result.gaussian_surface for result in bgs_results)
    context = prepare_vgss_sampling(
        surfaces,
        importance_function=importance_function,
        upper_bound=upper_bound,
        abs_tol=abs_tol,
    )

    return NetVGSS(
        net=net,
        bgs_results=tuple(bgs_results),
        sampling_context=context,
    )


def build_all_net_vgss(
    conductors: Sequence[Conductor],
    *,
    scale_factor: float = 1.0,
    max_distance: float = 10.0,
    importance_function: ImportanceFunction = uniform_importance,
    upper_bound: float = 1.0,
    abs_tol: float = 1e-12,
) -> tuple[NetVGSS, ...]:
    """Detect every net and prepare one independent VGSS for each net."""

    nets = find_touching_nets(conductors, abs_tol=abs_tol)
    return tuple(
        build_net_vgss(
            net,
            conductors,
            scale_factor=scale_factor,
            max_distance=max_distance,
            importance_function=importance_function,
            upper_bound=upper_bound,
            abs_tol=abs_tol,
        )
        for net in nets
    )


def build_vgss_for_conductor(
    conductors: Sequence[Conductor],
    conductor_name: str,
    *,
    scale_factor: float = 1.0,
    max_distance: float = 10.0,
    importance_function: ImportanceFunction = uniform_importance,
    upper_bound: float = 1.0,
    abs_tol: float = 1e-12,
) -> NetVGSS:
    """Prepare the VGSS for the net containing a selected conductor block."""

    nets = find_touching_nets(conductors, abs_tol=abs_tol)
    net = find_net_containing(nets, conductor_name)
    return build_net_vgss(
        net,
        conductors,
        scale_factor=scale_factor,
        max_distance=max_distance,
        importance_function=importance_function,
        upper_bound=upper_bound,
        abs_tol=abs_tol,
    )
