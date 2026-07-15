#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from wifi_datahub.catalog import load_tasks, validate_catalog  # noqa: E402
from wifi_datahub.task_profiles import TASK_PROFILES, profile_for_task  # noqa: E402


def infer_collection(dataset: dict) -> dict:
    hardware = dataset.get("hardware") or {}
    settings = dataset.get("settings") or {}
    scale = dataset.get("scale") or {}
    labels = {}
    for key in ("activities", "classes", "gesture_classes", "risk_classes", "har_classes", "identity_classes"):
        if key in scale:
            labels[key] = scale[key]
    for key in ("activity_instances", "locations", "zones", "max_people_count"):
        if key in scale:
            labels[key] = scale[key]
    sample_rate = (
        scale.get("nominal_sample_rate_hz")
        or scale.get("released_sample_rate_hz")
        or "Not reported; task profile supplies the derived-view rate"
    )
    return {
        "device": hardware.get("platform"),
        "subjects": settings.get("subjects") if settings.get("subjects") is not None else "Not reported",
        "labels": labels or "See dataset task tags and source documentation",
        "scenario_labels": settings.get("scenario"),
        "band": hardware.get("band") or "Not reported",
        "subcarriers": scale.get("subcarriers") or "Native to release / adapter",
        "sampling_rate_hz": sample_rate,
        "clip_length": (
            f"{scale['sample_seconds']} s" if "sample_seconds" in scale
            else f"{scale['window_seconds']} s" if "window_seconds" in scale
            else f"{scale['approx_seconds_per_sample']} s" if "approx_seconds_per_sample" in scale
            else "Task-profile view controls fixed intervals"
        ),
        "scenario": settings.get("scenario"),
    }


def task_profile_defaults(dataset: dict) -> list[dict]:
    rows = []
    seen = set()
    for task in dataset.get("tasks", []):
        profile = profile_for_task(task)
        if profile.id in seen:
            continue
        seen.add(profile.id)
        rows.append({
            "profile": profile.id,
            "description": profile.description,
            "target_rate_hz": profile.target_rate_hz,
            "duration_s": profile.duration_s,
            "interpolation": profile.interpolation,
            "layout": profile.layout,
        })
    return rows


def main() -> int:
    datasets, errors = validate_catalog(ROOT)
    if errors:
        print("Catalog validation failed:")
        print("\n".join(f"- {error}" for error in errors))
        return 1
    tasks = load_tasks(ROOT)
    adapters = json.loads((ROOT / "catalog" / "adapters.json").read_text(encoding="utf-8"))["datasets"]
    splits = json.loads((ROOT / "catalog" / "splits.json").read_text(encoding="utf-8"))["datasets"]
    examples = json.loads((ROOT / "catalog" / "examples.json").read_text(encoding="utf-8"))["datasets"]
    for dataset in datasets:
        dataset["conversion"] = adapters[dataset["id"]]
        dataset["split_settings"] = splits[dataset["id"]]
        dataset["conversion_example"] = examples[dataset["id"]]
        dataset["collection"] = dataset.get("collection") or infer_collection(dataset)
        dataset["task_profile_defaults"] = task_profile_defaults(dataset)
    task_counts = Counter(task for dataset in datasets for task in dataset["tasks"])
    payload = {
        "generated_at": "2026-07-01",
        "datasets": datasets,
        "tasks": [{**item, "dataset_count": task_counts[item["id"]]} for item in tasks.values()],
        "stats": {
            "datasets": len(datasets),
            "tasks": len(tasks),
            "hardware_platforms": len({dataset["hardware"]["platform"] for dataset in datasets}),
            "open_or_direct": sum(dataset["original"]["access"] == "direct" for dataset in datasets),
        },
    }
    destination = ROOT / "site" / "data" / "catalog.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {destination.relative_to(ROOT)} with {len(datasets)} datasets")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
