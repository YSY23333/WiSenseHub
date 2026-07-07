from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_mmfi_directory


def convert(input_path: Path, output_path: Path) -> Path:
    if not input_path.is_dir():
        raise ValueError("MM-Fi adapter expects an official wifi-csi frame directory")
    return convert_mmfi_directory(input_path, output_path)
