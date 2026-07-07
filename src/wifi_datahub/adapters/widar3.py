from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_widar_csv


def convert(input_path: Path, output_path: Path) -> Path:
    if input_path.suffix.lower() != ".csv":
        raise ValueError("Widar3 adapter expects official SenseFi BVP CSV input")
    return convert_widar_csv(input_path, output_path)
