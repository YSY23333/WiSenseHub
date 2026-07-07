from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_wimans


def convert(input_path: Path, output_path: Path) -> Path:
    if input_path.suffix.lower() not in {".mat", ".npy"}:
        raise ValueError("WiMANS adapter expects MAT or NPY WiFi CSI input")
    return convert_wimans(input_path, output_path)
