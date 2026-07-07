from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Tuple

import numpy as np


ACTIVITY_NAMES = ["hand_up", "hand_down", "hand_left", "hand_right", "hand_circle", "hand_cross"]


def normalize_aril_arrays(
    data: np.ndarray,
    activity_label: np.ndarray,
    location_label: np.ndarray,
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """Convert official ARIL arrays to [sample, time, link, subcarrier].

    The official model consumes `[sample, 52, 192]`, where 52 is the
    subcarrier/channel axis and 192 is the packet axis.
    """
    data = np.asarray(data)
    if data.ndim != 3:
        raise ValueError(f"ARIL data must be 3-D, got {data.shape}")
    if data.shape[1:] == (52, 192):
        canonical = data.transpose(0, 2, 1)[:, :, None, :]
    elif data.shape[1:] == (192, 52):
        canonical = data[:, :, None, :]
    else:
        raise ValueError(f"expected ARIL sample shape 52×192 or 192×52, got {data.shape[1:]}")
    activity = np.asarray(activity_label).reshape(-1).astype(np.int16)
    location = np.asarray(location_label).reshape(-1).astype(np.int16)
    if canonical.shape[0] != activity.size or canonical.shape[0] != location.size:
        raise ValueError("ARIL data and label counts differ")
    return canonical.astype(np.float32), activity, location


def convert_aril_mat(input_path: Path, output_path: Path, split: str) -> Path:
    try:
        from scipy.io import loadmat  # type: ignore
    except ImportError as exc:
        raise RuntimeError("ARIL MAT conversion requires the optional 'scipy' dependency") from exc
    payload: Dict[str, np.ndarray] = loadmat(input_path)
    prefix = "train" if split == "train" else "test"
    amplitude, activity, location = normalize_aril_arrays(
        payload[f"{prefix}_data"],
        payload[f"{prefix}_activity_label"],
        payload[f"{prefix}_location_label"],
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    packet_index = np.arange(amplitude.shape[1], dtype=np.int32)
    valid_mask = np.ones(amplitude.shape[:2], dtype=bool)
    np.savez_compressed(
        output_path,
        packet_index=packet_index,
        amplitude=amplitude,
        valid_mask=valid_mask,
        activity_label=activity,
        location_label=location,
    )
    digest = hashlib.sha256(input_path.read_bytes()).hexdigest()
    sidecar = {
        "schema_version": "1.0",
        "dataset_id": "aril",
        "split": split,
        "source_file": input_path.name,
        "source_sha256": digest,
        "source_representation": "processed_amplitude",
        "standard_representation": "amplitude",
        "shape": list(amplitude.shape),
        "axis_order": ["sample", "packet", "link", "subcarrier"],
        "sample_rate_hz": None,
        "time_axis": "packet_index",
        "power_unit": "source_amplitude_arbitrary_unit",
        "labels": {"activity": ACTIVITY_NAMES, "location": "integer 0-15"},
        "transformations": ["transpose channel and packet axes", "insert link axis", "cast float32"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "wisensehub-0.6.0",
    }
    sidecar_path = output_path.with_suffix(".json")
    sidecar_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    return sidecar_path
