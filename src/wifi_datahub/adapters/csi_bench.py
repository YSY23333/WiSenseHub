from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_csi_bench_mat


def convert(input_path: Path, output_path: Path) -> Path:
    if input_path.suffix.lower() not in {".mat", ".h5", ".hdf5"}:
        raise ValueError("CSI-Bench adapter expects MAT/HDF5 input")
    return convert_csi_bench_mat(input_path, output_path)
