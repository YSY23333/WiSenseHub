from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_usrp_amplitude_csv


def convert(input_path: Path, output_path: Path) -> Path:
    if input_path.suffix.lower() != ".csv":
        raise ValueError("WiPE-FaLl adapter expects CSV amplitude input")
    return convert_usrp_amplitude_csv("wipe-fall", input_path, output_path)
