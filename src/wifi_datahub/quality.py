from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np


def inspect_npz(path: Path) -> Dict[str, Any]:
    arrays = np.load(path, allow_pickle=False)
    report: Dict[str, Any] = {"file": path.name, "arrays": {}}
    for name in arrays.files:
        value = arrays[name]
        item: Dict[str, Any] = {"shape": list(value.shape), "dtype": str(value.dtype)}
        if np.issubdtype(value.dtype, np.number):
            item["nan_count"] = int(np.isnan(value).sum()) if np.issubdtype(value.dtype, np.floating) else 0
            finite = value[np.isfinite(value)] if np.issubdtype(value.dtype, np.floating) else value.reshape(-1)
            if finite.size:
                item.update({"min": float(np.min(finite)), "max": float(np.max(finite)), "mean": float(np.mean(finite))})
        if name == "valid_mask":
            item["valid_fraction"] = float(np.mean(value))
        report["arrays"][name] = item
    return report


def write_quality_report(input_path: Path, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(inspect_npz(input_path), indent=2) + "\n", encoding="utf-8")

