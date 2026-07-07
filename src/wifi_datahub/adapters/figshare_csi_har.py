from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_three_rooms_directory


def convert(input_path: Path, output_path: Path) -> Path:
    if input_path.name != "data.csv":
        raise ValueError("Figshare CSI-HAR adapter expects an official data.csv file")
    return convert_three_rooms_directory(input_path, output_path)
