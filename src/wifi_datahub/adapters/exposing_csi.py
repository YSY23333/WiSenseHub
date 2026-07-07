from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_exposing_csi_mat


def convert(input_path: Path, output_path: Path) -> Path:
    if input_path.suffix.lower() != ".mat":
        raise ValueError("Exposing-CSI adapter expects MAT input")
    return convert_exposing_csi_mat(input_path, output_path)
