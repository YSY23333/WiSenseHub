from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_csida_zarr


def convert(input_path: Path, output_path: Path) -> Path:
    if not input_path.is_dir():
        raise ValueError("CSIDA adapter expects the official csi_data_amp Zarr directory")
    return convert_csida_zarr(input_path, output_path)
