from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_xrf55_npy


def convert(input_path: Path, output_path: Path) -> Path:
    if input_path.suffix.lower() != ".npy":
        raise ValueError("XRF55 adapter expects NPY WiFi input")
    return convert_xrf55_npy(input_path, output_path)
