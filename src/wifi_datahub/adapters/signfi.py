from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_signfi_mat


def convert(input_path: Path, output_path: Path) -> Path:
    if input_path.suffix.lower() != ".mat":
        raise ValueError("SignFi adapter expects MAT input")
    return convert_signfi_mat(input_path, output_path)
