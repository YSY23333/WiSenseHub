from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_wifi_80mhz_mat


def convert(input_path: Path, output_path: Path) -> Path:
    if input_path.suffix.lower() != ".mat":
        raise ValueError("WiFi-80MHz adapter expects MAT input")
    return convert_wifi_80mhz_mat(input_path, output_path)
