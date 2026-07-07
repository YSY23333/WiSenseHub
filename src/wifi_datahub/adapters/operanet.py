from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_operanet_mat


def convert(input_path: Path, output_path: Path) -> Path:
    if input_path.suffix.lower() != ".mat":
        raise ValueError("OPERAnet adapter expects MAT input")
    return convert_operanet_mat(input_path, output_path)
