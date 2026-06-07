from __future__ import annotations

import re
from pathlib import Path

import numpy as np

from .models import Bounds, Conductor

_ASSIGNMENT_RE = re.compile(
    r"(?P<name>[A-Za-z_]\w*)\s*=\s*\[(?P<body>.*?)\]\s*;",
    re.DOTALL,
)
_EPS_RE = re.compile(r"eps_r\s*=\s*([-+]?\d+(?:\.\d*)?(?:[eE][-+]?\d+)?)")
_NUMBER_RE = re.compile(r"[-+]?(?:\d+(?:\.\d*)?|\.\d+)(?:[eE][-+]?\d+)?")


class MatlabGeometryParseError(ValueError):
    """Raised when a MATLAB geometry block cannot be parsed safely."""


def _parse_matrix(body: str, variable_name: str) -> np.ndarray:
    rows: list[list[float]] = []

    # Remove MATLAB comments line-by-line before splitting rows. A comment placed
    # after a semicolon must not swallow the numeric row on the following line.
    uncommented_body = "\n".join(
        line.split("%", maxsplit=1)[0]
        for line in body.splitlines()
    )

    for raw_row in uncommented_body.split(";"):
        if not raw_row.strip():
            continue
        values = [float(token) for token in _NUMBER_RE.findall(raw_row)]
        if values:
            rows.append(values)

    if not rows:
        raise MatlabGeometryParseError(f"{variable_name}: no numeric rows found.")

    row_lengths = {len(row) for row in rows}
    if row_lengths != {12}:
        raise MatlabGeometryParseError(
            f"{variable_name}: expected 12 numbers per face row, found row lengths "
            f"{sorted(row_lengths)}."
        )

    matrix = np.asarray(rows, dtype=float)
    if matrix.shape[0] != 6:
        raise MatlabGeometryParseError(
            f"{variable_name}: expected 6 face rows for a cuboid, found {matrix.shape[0]}."
        )
    return matrix.reshape(6, 4, 3)


def parse_matlab_geometry(path: str | Path) -> list[Conductor]:
    """Parse matrices such as C1 = [ ... ]; from a MATLAB-style geometry file."""

    file_path = Path(path)
    text = file_path.read_text(encoding="utf-8")

    conductors: list[Conductor] = []
    previous_end = 0

    for match in _ASSIGNMENT_RE.finditer(text):
        name = match.group("name")
        prefix = text[previous_end : match.start()]
        eps_matches = list(_EPS_RE.finditer(prefix))
        eps_r = float(eps_matches[-1].group(1)) if eps_matches else None

        faces = _parse_matrix(match.group("body"), name)
        bounds = Bounds.from_vertices(faces)
        conductors.append(
            Conductor(
                name=name,
                bounds=bounds,
                face_vertices=faces,
                relative_permittivity=eps_r,
            )
        )
        previous_end = match.end()

    if not conductors:
        raise MatlabGeometryParseError(
            f"No conductor matrices were found in {file_path}."
        )

    names = [conductor.name for conductor in conductors]
    if len(names) != len(set(names)):
        raise MatlabGeometryParseError("Duplicate conductor names were found.")

    return conductors
