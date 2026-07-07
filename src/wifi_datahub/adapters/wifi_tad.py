from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_wifi_tad_npy


def convert(input_path: Path, output_path: Path) -> Path:
    if input_path.suffix.lower() != ".npy":
        raise ValueError("WiFiTAD adapter expects official smartwifi NPY input")
    return convert_wifi_tad_npy(input_path, output_path)
