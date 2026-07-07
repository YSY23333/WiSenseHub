from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_nist_breathesmart


def convert(input_path: Path, output_path: Path) -> Path:
    if not input_path.name.endswith("_csi_real_log.csv"):
        raise ValueError("NIST BreatheSmart adapter expects *_csi_real_log.csv input")
    return convert_nist_breathesmart(input_path, output_path)
