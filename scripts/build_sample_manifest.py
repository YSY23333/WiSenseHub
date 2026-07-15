#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import zipfile
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / "site"
PREVIEWS = SITE / "assets" / "previews"
FIGURES = SITE / "assets" / "figures"
SAMPLES = SITE / "samples"


TASK_LABEL_HINTS = {
    "har": "walking / sitting / standing / no_person",
    "gesture": "one gesture class",
    "fall": "fall / non_fall",
    "vital_sign": "one breathing or respiration label",
    "occupancy": "empty / occupied or people-count label",
    "spatial_localization": "one room / location / zone label",
    "identity": "one subject ID",
    "tad_tal": "one temporal action segment",
    "motion_source": "one motion-source label",
    "machine_sensing": "one machine-state label",
    "pose": "one pose/action label",
    "multitask": "one primary task label plus its auxiliary labels",
}


def slug_label(path: Path) -> str:
    name = path.stem
    return re.sub(r"^label_", "", name).replace("_", " ")


def file_tree(root: Path) -> list[dict]:
    if not root.exists():
        return []
    entries = []
    for path in sorted(root.iterdir(), key=lambda p: (p.is_file(), p.name)):
        if path.is_dir():
            entries.append({"name": path.name, "type": "dir", "children": file_tree(path)})
        else:
            entries.append({"name": path.name, "type": "file", "bytes": path.stat().st_size})
    return entries


def zip_file_tree(path: Path) -> list[dict]:
    """Build the same tree schema from a hosted sample ZIP.

    GitHub Pages publishes only the compact ZIP rather than the duplicate
    extracted sample directory, so the website must be able to describe the
    sample without relying on local extraction artifacts.
    """
    if not path.exists():
        return []
    root: dict[str, dict] = {}
    with zipfile.ZipFile(path) as handle:
        for item in handle.infolist():
            if item.is_dir():
                continue
            cursor = root
            parts = [part for part in Path(item.filename).parts if part not in {".", "/"}]
            for part in parts[:-1]:
                cursor = cursor.setdefault(part, {})
            if parts:
                cursor[parts[-1]] = {"__file_bytes__": item.file_size}

    def render(nodes: dict[str, dict]) -> list[dict]:
        entries = []
        for name in sorted(nodes):
            node = nodes[name]
            if "__file_bytes__" in node:
                entries.append({"name": name, "type": "file", "bytes": node["__file_bytes__"]})
            else:
                entries.append({"name": name, "type": "dir", "children": render(node)})
        return entries

    return render(root)


def count_files(root: Path) -> int:
    return sum(1 for path in root.rglob("*") if path.is_file()) if root.exists() else 0


def zip_stats(path: Path) -> tuple[int, int]:
    if not path.exists():
        return 0, 0
    with zipfile.ZipFile(path) as handle:
        return len([item for item in handle.infolist() if not item.is_dir()]), path.stat().st_size


def sample_requirement(dataset: dict) -> dict:
    tasks = dataset.get("tasks") or []
    primary = tasks[0] if tasks else "task"
    split = dataset.get("split_settings") or {}
    setting = split.get("default") or "default"
    return {
        "task": primary,
        "task_label": TASK_LABEL_HINTS.get(primary, "one representative label"),
        "setting": setting,
        "setting_note": "Use the default split/setting unless the dataset paper specifies a stricter protocol.",
    }


def commands(dataset_id: str, default_setting: str, task: str) -> list[str]:
    return [
        f"Place the official release under data/{dataset_id}/original/",
        f"wisensehub prepare {dataset_id} --data-root data --setting {default_setting} --task {task} --limit 1",
        f"python scripts/build_sample_manifest.py",
    ]


def main() -> int:
    catalog = json.loads((SITE / "data" / "catalog.json").read_text(encoding="utf-8"))
    figure_sources_path = FIGURES / "sources.json"
    figure_sources = json.loads(figure_sources_path.read_text(encoding="utf-8")) if figure_sources_path.exists() else {}
    payload: dict[str, dict] = {}
    for dataset in catalog["datasets"]:
        dataset_id = dataset["id"]
        requirement = sample_requirement(dataset)
        default_setting = requirement["setting"]
        task = requirement["task"]
        preview_dir = PREVIEWS / dataset_id
        zip_path = SAMPLES / f"{dataset_id}.zip"
        sample_dir = SAMPLES / dataset_id
        label_previews = [
            {
                "label": slug_label(path),
                "slug": path.stem.replace("label_", ""),
                "image": f"assets/previews/{dataset_id}/{path.name}",
                "kind": "clip",
            }
            for path in sorted(preview_dir.glob("label_*.png"))
        ]
        sample_count, zip_bytes = zip_stats(zip_path)
        has_zip = zip_path.exists()
        entry = {
            "status": "ok" if has_zip else "planned",
            "note": (
                "Small structure-preserving sample is hosted for this dataset."
                if has_zip else
                "No redistributable hosted sample is included yet. The page still records the required task label, setting, and local generation command."
            ),
            "sample_requirement": requirement,
            "local_generation": commands(dataset_id, default_setting, task),
            "sample_zip": f"samples/{dataset_id}.zip" if has_zip else None,
            "zip_bytes": zip_bytes or None,
            "file_count": sample_count or count_files(sample_dir),
            "file_tree": file_tree(sample_dir) if sample_dir.exists() else zip_file_tree(zip_path),
            "previews": {},
            "label_previews": label_previews,
            "label_coverage": {
                "expected": "at least one standardized preview for each task label",
                "available": len(label_previews),
                "complete": bool(label_previews),
            },
        }
        before = preview_dir / "before.png"
        after = preview_dir / "after.png"
        if before.exists():
            entry["previews"]["before"] = f"assets/previews/{dataset_id}/before.png"
        if after.exists():
            entry["previews"]["after"] = f"assets/previews/{dataset_id}/after.png"
        figures = sorted(FIGURES.glob(f"{dataset_id}*.png"))
        if figures:
            entry["setup_figures"] = [
                {
                    "image": f"assets/figures/{figure.name}",
                    "source": figure_sources.get(figure.stem) or figure_sources.get(dataset_id),
                }
                for figure in figures
            ]
        payload[dataset_id] = entry
    destination = SITE / "data" / "samples.json"
    destination.write_text(json.dumps({"schema_version": "1.0", "datasets": payload}, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Wrote {destination.relative_to(ROOT)} with {len(payload)} sample entries")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
