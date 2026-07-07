from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

from .io import load_csi_csv


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def _prepare_time(timestamp: np.ndarray, real: np.ndarray, imag: np.ndarray) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    if timestamp.ndim != 1 or real.shape != imag.shape or real.shape[0] != timestamp.size:
        raise ValueError("timestamp and CSI dimensions are inconsistent")
    finite = np.isfinite(timestamp)
    timestamp, real, imag = timestamp[finite], real[finite], imag[finite]
    order = np.argsort(timestamp, kind="stable")
    timestamp, real, imag = timestamp[order], real[order], imag[order]
    timestamp, unique_indices = np.unique(timestamp, return_index=True)
    real, imag = real[unique_indices], imag[unique_indices]
    if timestamp.size < 2:
        raise ValueError("at least two unique timestamps are required")
    timestamp = timestamp - timestamp[0]
    return timestamp, real, imag


def resample_csi(
    timestamp: np.ndarray,
    real: np.ndarray,
    imag: np.ndarray,
    sample_rate_hz: float,
    duration_s: Optional[float] = None,
) -> Dict[str, np.ndarray]:
    timestamp, real, imag = _prepare_time(timestamp, real, imag)
    if sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive")
    duration_s = float(duration_s if duration_s is not None else timestamp[-1] + 1.0 / sample_rate_hz)
    if duration_s <= 0:
        raise ValueError("duration_s must be positive")
    count = max(1, int(round(duration_s * sample_rate_hz)))
    target = np.arange(count, dtype=np.float64) / sample_rate_hz
    flat_real = real.reshape(real.shape[0], -1)
    flat_imag = imag.reshape(imag.shape[0], -1)
    out_real = np.empty((count, flat_real.shape[1]), dtype=np.float32)
    out_imag = np.empty_like(out_real)
    for column in range(flat_real.shape[1]):
        out_real[:, column] = np.interp(target, timestamp, flat_real[:, column]).astype(np.float32)
        out_imag[:, column] = np.interp(target, timestamp, flat_imag[:, column]).astype(np.float32)
    out_real = out_real.reshape((count,) + real.shape[1:])
    out_imag = out_imag.reshape((count,) + imag.shape[1:])

    insertion = np.searchsorted(timestamp, target)
    left = np.clip(insertion - 1, 0, timestamp.size - 1)
    right = np.clip(insertion, 0, timestamp.size - 1)
    nearest = np.minimum(np.abs(target - timestamp[left]), np.abs(target - timestamp[right]))
    median_dt = float(np.median(np.diff(timestamp)))
    tolerance = max(1.5 / sample_rate_hz, 1.5 * median_dt)
    valid = (target >= timestamp[0]) & (target <= timestamp[-1]) & (nearest <= tolerance)
    out_real[~valid] = 0
    out_imag[~valid] = 0

    amplitude = np.hypot(out_real, out_imag).astype(np.float32)
    power = amplitude.astype(np.float64) ** 2
    reference = float(np.median(power[valid])) if np.any(valid) else 1.0
    reference = max(reference, np.finfo(np.float32).tiny)
    power_db_rel = (10.0 * np.log10(np.maximum(power, np.finfo(np.float32).tiny) / reference)).astype(np.float32)
    power_db_rel[~valid] = 0
    return {
        "timestamp_s": target,
        "csi_real": out_real,
        "csi_imag": out_imag,
        "amplitude": amplitude,
        "power_db_rel": power_db_rel,
        "valid_mask": valid,
        "reference_power": np.asarray(reference, dtype=np.float64),
    }


def standardize_csv(
    input_path: Path,
    output_path: Path,
    dataset_id: str,
    sample_rate_hz: float = 100.0,
    duration_s: Optional[float] = None,
) -> Path:
    timestamp, real, imag, representation = load_csi_csv(input_path)
    arrays = resample_csi(timestamp, real, imag, sample_rate_hz, duration_s)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, **arrays)
    metadata: Dict[str, Any] = {
        "schema_version": "1.0",
        "dataset_id": dataset_id,
        "source_file": input_path.name,
        "source_sha256": sha256_file(input_path),
        "source_representation": representation,
        "standard_representation": "complex_csi" if representation == "complex_csi" else "amplitude_as_real_component",
        "shape": list(arrays["csi_real"].shape),
        "sample_rate_hz": sample_rate_hz,
        "duration_s": float(arrays["timestamp_s"].size / sample_rate_hz),
        "time_unit": "s",
        "power_unit": "dB_relative_to_median_valid_sample_power",
        "valid_fraction": float(np.mean(arrays["valid_mask"])),
        "transformations": ["sort timestamps", "drop duplicate timestamps", "linear interpolation of real/imag", "fixed interval crop/pad", "relative-power conversion"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "wisensehub-0.6.0",
    }
    sidecar = output_path.with_suffix(".json")
    sidecar.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return sidecar
