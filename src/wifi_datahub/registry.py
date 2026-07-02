from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

from .catalog import repository_root


def _load_catalog_file(name: str, root: Path | None = None) -> Dict[str, Any]:
    base = root or repository_root()
    return json.loads((base / "catalog" / name).read_text(encoding="utf-8"))["datasets"]


def load_adapter_registry(root: Path | None = None) -> Dict[str, Dict[str, Any]]:
    return _load_catalog_file("adapters.json", root)


def load_split_registry(root: Path | None = None) -> Dict[str, Dict[str, Any]]:
    return _load_catalog_file("splits.json", root)


def get_split_setting(dataset_id: str, setting_id: str | None = None) -> Dict[str, Any]:
    datasets = load_split_registry()
    if dataset_id not in datasets:
        raise ValueError(f"no split settings registered for {dataset_id}")
    dataset = datasets[dataset_id]
    selected = setting_id or dataset["default"]
    for setting in dataset["settings"]:
        if setting["id"] == selected:
            return setting
    choices = ", ".join(item["id"] for item in dataset["settings"])
    raise ValueError(f"unknown setting {selected!r} for {dataset_id}; choose one of: {choices}")
