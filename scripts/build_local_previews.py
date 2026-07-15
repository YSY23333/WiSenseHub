#!/usr/bin/env python3
"""Build sample zips and CSI heatmaps from already prepared local datasets.

This script is intentionally conservative: it only uses files that already
exist under ``data/<dataset-id>/``. It does not download official releases.
Run ``wisensehub prepare <dataset-id>`` first, then run this script to mirror a
small original/standardized subset into ``site/samples`` and render preview
figures into ``site/assets/previews``.
"""
from __future__ import annotations

import argparse
import csv
import gzip
import json
import shutil
import sys
import zipfile
from pathlib import Path
from typing import Iterable, Optional, Sequence

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from PIL import Image, ImageDraw, ImageFont  # noqa: E402

DATA = ROOT / "data"
SITE = ROOT / "site"
SAMPLES = SITE / "samples"
PREVIEWS = SITE / "assets" / "previews"


UT_HAR_LABELS = ["lie_down", "fall", "walk", "pickup", "run", "sit_down", "stand_up"]


def load_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def resolve(path: str) -> Path:
    p = Path(path)
    return p if p.is_absolute() else ROOT / p


def first_record(dataset_id: str) -> Optional[dict]:
    manifest = DATA / dataset_id / "prepare-manifest.json"
    if not manifest.exists():
        return None
    records = load_json(manifest).get("records") or []
    return next((item for item in records if item.get("output")), None)


def source_paths(record: dict) -> list[Path]:
    paths = []
    for key in ("source", "output", "native_output"):
        value = record.get(key)
        if value:
            path = resolve(value)
            if path.exists():
                paths.append(path)
                sidecar = path.with_suffix(".json") if path.is_file() else None
                if sidecar and sidecar.exists():
                    paths.append(sidecar)
    return paths


def copy_subset(dataset_id: str, record: dict) -> None:
    sample_root = SAMPLES / dataset_id
    if sample_root.exists():
        shutil.rmtree(sample_root)
    original_root = DATA / dataset_id / "original"
    standardized_root = DATA / dataset_id / "standardized"
    for path in source_paths(record):
        if path.is_relative_to(original_root):
            target = sample_root / "original" / path.relative_to(original_root)
        elif path.is_relative_to(standardized_root):
            target = sample_root / "standardized" / path.relative_to(standardized_root)
        else:
            target = sample_root / path.name
        target.parent.mkdir(parents=True, exist_ok=True)
        if path.is_dir():
            if target.exists():
                shutil.rmtree(target)
            shutil.copytree(path, target)
        else:
            shutil.copy2(path, target)


def zip_sample(dataset_id: str) -> tuple[int, int, int]:
    sample_root = SAMPLES / dataset_id
    zip_path = SAMPLES / f"{dataset_id}.zip"
    zip_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as handle:
        for path in sorted(sample_root.rglob("*")):
            if path.is_file():
                handle.write(path, Path(dataset_id) / path.relative_to(sample_root))
    files = [path for path in sample_root.rglob("*") if path.is_file()]
    return len(files), sum(path.stat().st_size for path in files), zip_path.stat().st_size


def matrix_from_npz(npz_path: Path, sidecar_path: Path) -> tuple[np.ndarray, Optional[float]]:
    sidecar = load_json(sidecar_path) if sidecar_path.exists() else {}
    axes = sidecar.get("axis_order") or []
    with np.load(npz_path, allow_pickle=False) as archive:
        key = sidecar.get("standard_representation")
        if key not in archive.files:
            key = "amplitude" if "amplitude" in archive.files else archive.files[0]
        tensor = np.asarray(archive[key], dtype=np.float64)
    if axes and axes[0] == "sample" and tensor.ndim >= 4:
        tensor = tensor[0]
        axes = axes[1:]
    if tensor.ndim == 3 and axes[:3] in (["time", "link", "subcarrier"], ["packet", "link", "subcarrier"]):
        matrix = tensor.transpose(1, 2, 0).reshape(-1, tensor.shape[0])
    elif tensor.ndim == 2:
        matrix = tensor.T
    else:
        matrix = tensor.reshape(tensor.shape[0], -1).T
    return matrix, sidecar.get("sample_rate_hz")


def render_heatmap(matrix: np.ndarray, fs: Optional[float], title: str, destination: Path) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    matrix = np.asarray(matrix, dtype=np.float64)
    if matrix.ndim == 1:
        matrix = matrix[None, :]
    finite = matrix[np.isfinite(matrix)]
    if finite.size:
        lo, hi = np.percentile(finite, [2, 98])
    else:
        lo, hi = 0.0, 1.0
    if hi <= lo:
        hi = lo + 1.0
    norm = np.clip((np.nan_to_num(matrix, nan=lo) - lo) / (hi - lo), 0.0, 1.0)
    # Lightweight viridis-like gradient: dark purple -> blue/green -> yellow.
    stops = np.asarray([
        [68, 1, 84],
        [59, 82, 139],
        [33, 145, 140],
        [94, 201, 98],
        [253, 231, 37],
    ], dtype=np.float32)
    scaled = norm * (len(stops) - 1)
    left = np.floor(scaled).astype(np.int32)
    right = np.clip(left + 1, 0, len(stops) - 1)
    weight = scaled - left
    rgb = (stops[left] * (1 - weight[..., None]) + stops[right] * weight[..., None]).astype(np.uint8)
    heat = Image.fromarray(rgb, mode="RGB").resize((660, 396), Image.Resampling.BILINEAR)
    canvas = Image.new("RGB", (760, 480), "white")
    draw = ImageDraw.Draw(canvas)
    font = ImageFont.load_default()
    draw.text((24, 14), f"{title}: CSI amplitude", fill=(20, 36, 31), font=font)
    draw.text((24, 444), f"x = time ({'s' if fs else 'packets'}), y = subcarrier / channel index", fill=(94, 109, 103), font=font)
    canvas.paste(heat, (50, 38))
    draw.rectangle((50, 38, 709, 433), outline=(216, 220, 211), width=1)
    destination.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(destination)


def raw_ut_har(path: Path) -> tuple[np.ndarray, Optional[float]]:
    data = np.load(path, allow_pickle=False)
    sample = np.asarray(data[0]).reshape(250, 3, 30)
    return sample.transpose(1, 2, 0).reshape(-1, 250), None


def raw_wifi_presence(path: Path) -> tuple[np.ndarray, Optional[float]]:
    opener = gzip.open if path.suffix == ".gz" else open
    packets = []
    with opener(path, "rt", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            csi = row.get("csi") or row.get("CSI") or row.get("data")
            if isinstance(csi, str):
                try:
                    csi = json.loads(csi)
                except json.JSONDecodeError:
                    continue
            if csi is not None:
                arr = np.asarray(csi, dtype=np.float32).reshape(-1)
                if arr.size:
                    packets.append(np.abs(arr))
            if len(packets) >= 300:
                break
    if not packets:
        raise ValueError("no CSI packets found in JSON sample")
    width = min(len(p) for p in packets)
    return np.stack([p[:width] for p in packets]).T, None


def raw_nist(path: Path) -> tuple[np.ndarray, Optional[float]]:
    real = np.genfromtxt(path, delimiter=",")
    imag_path = path.with_name(path.name.replace("_csi_real_log.csv", "_csi_imag_log.csv"))
    imag = np.genfromtxt(imag_path, delimiter=",")
    return np.hypot(np.atleast_2d(real), np.atleast_2d(imag)).T, 10.0


def raw_from_source(dataset_id: str, source: Path) -> Optional[tuple[np.ndarray, Optional[float]]]:
    if dataset_id == "nist-breathesmart":
        return raw_nist(source)
    if dataset_id == "ut-har":
        return raw_ut_har(source)
    if dataset_id == "wifi-presence-movement":
        return raw_wifi_presence(source)
    if source.suffix == ".npz":
        return matrix_from_npz(source, source.with_suffix(".json"))
    return None


def label_entries(dataset_id: str, npz_path: Path, sidecar_path: Path) -> list[tuple[str, np.ndarray, Optional[float]]]:
    sidecar = load_json(sidecar_path) if sidecar_path.exists() else {}
    with np.load(npz_path, allow_pickle=False) as archive:
        if "activity_label" in archive.files and "amplitude" in archive.files:
            labels = np.asarray(archive["activity_label"]).reshape(-1)
            data = np.asarray(archive["amplitude"])
            out = []
            for label_id in sorted(set(int(x) for x in labels.tolist())):
                index = int(np.where(labels == label_id)[0][0])
                name = UT_HAR_LABELS[label_id] if 0 <= label_id < len(UT_HAR_LABELS) else str(label_id)
                sample = data[index]
                matrix = sample.transpose(1, 2, 0).reshape(-1, sample.shape[0])
                out.append((name, matrix, sidecar.get("sample_rate_hz")))
            return out
        if "source_label" in archive.files:
            labels = np.asarray(archive["source_label"]).reshape(-1)
            if labels.size:
                matrix, fs = matrix_from_npz(npz_path, sidecar_path)
                return [(str(labels[0]), matrix, fs)]
        for key in ("config_pattern", "config_bpm"):
            if key in archive.files:
                value = str(np.asarray(archive[key]).reshape(-1)[0])
                if value:
                    label = value if key == "config_pattern" else f"{value}_bpm"
                    matrix, fs = matrix_from_npz(npz_path, sidecar_path)
                    return [(label, matrix, fs)]
    label_map = sidecar.get("labels") or {}
    if isinstance(label_map.get("activity"), str):
        matrix, fs = matrix_from_npz(npz_path, sidecar_path)
        return [(label_map["activity"], matrix, fs)]
    if isinstance(label_map.get("pattern"), str):
        matrix, fs = matrix_from_npz(npz_path, sidecar_path)
        return [(label_map["pattern"], matrix, fs)]
    if dataset_id == "wifi-presence-movement":
        matrix, fs = matrix_from_npz(npz_path, sidecar_path)
        return [("presence_movement_sample", matrix, fs)]
    if dataset_id == "nist-breathesmart":
        matrix, fs = matrix_from_npz(npz_path, sidecar_path)
        return [("breathing_pattern", matrix, fs)]
    return []


def slug(value: str) -> str:
    import re

    return re.sub(r"[^a-z0-9]+", "_", value.lower()).strip("_") or "unknown"


def write_fetch_report(dataset_id: str, files: int, bytes_: int, zip_bytes: int) -> None:
    report_path = SAMPLES / "fetch-report.json"
    report = load_json(report_path) if report_path.exists() else {}
    report[dataset_id] = {
        "status": "ok",
        "note": "Sample generated from local official files already placed under data/<dataset-id>/original/.",
        "files": files,
        "bytes": bytes_,
        "zip_bytes": zip_bytes,
    }
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def build_dataset(dataset_id: str) -> bool:
    record = first_record(dataset_id)
    if not record:
        print(f"[local-previews] {dataset_id}: no prepare manifest")
        return False
    copy_subset(dataset_id, record)
    preview_dir = PREVIEWS / dataset_id
    preview_dir.mkdir(parents=True, exist_ok=True)
    output = resolve(record["output"])
    sidecar = output.with_suffix(".json")
    native = resolve(record.get("native_output") or record["output"])
    native_sidecar = native.with_suffix(".json")
    source = resolve(record["source"])
    try:
        raw = raw_from_source(dataset_id, source)
        if raw:
            render_heatmap(raw[0], raw[1], "Original", preview_dir / "before.png")
        else:
            render_heatmap(*matrix_from_npz(native, native_sidecar), "Original/native", preview_dir / "before.png")
    except Exception as exc:  # noqa: BLE001
        try:
            render_heatmap(*matrix_from_npz(native, native_sidecar), "Original/native", preview_dir / "before.png")
            print(f"[local-previews] {dataset_id}: raw before failed; used native standardized preview ({exc})")
        except Exception:
            print(f"[local-previews] {dataset_id}: before preview skipped ({exc})")
    render_heatmap(*matrix_from_npz(output, sidecar), "Standardized view", preview_dir / "after.png")
    for label, matrix, fs in label_entries(dataset_id, native, native_sidecar):
        render_heatmap(matrix, fs, label, preview_dir / f"label_{slug(label)}.png")
    files, bytes_, zip_bytes = zip_sample(dataset_id)
    write_fetch_report(dataset_id, files, bytes_, zip_bytes)
    print(f"[local-previews] {dataset_id}: ready ({files} files)")
    return True


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("datasets", nargs="*", help="dataset ids; default: every data/<id>/prepare-manifest.json")
    args = parser.parse_args(argv)
    datasets = args.datasets or sorted(path.parent.name for path in DATA.glob("*/prepare-manifest.json"))
    ok = 0
    for dataset_id in datasets:
        ok += int(build_dataset(dataset_id))
    print(f"[local-previews] built {ok}/{len(datasets)} dataset sample previews")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
