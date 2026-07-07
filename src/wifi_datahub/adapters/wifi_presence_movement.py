from __future__ import annotations

from pathlib import Path

from .official_profiles import convert_wifi_presence_json


def convert(input_path: Path, output_path: Path) -> Path:
    if not (input_path.name.endswith(".json.gz") or input_path.suffix.lower() == ".json"):
        raise ValueError("WiFi presence/movement adapter expects JSON or JSON.GZ CSI records")
    return convert_wifi_presence_json(input_path, output_path)
