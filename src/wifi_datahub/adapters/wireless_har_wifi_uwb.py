from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_wireless_har_wifi


def convert(input_path: Path, output_path: Path) -> Path:
    return convert_wireless_har_wifi(input_path, output_path)
