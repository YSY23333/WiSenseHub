from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Sequence, Tuple

import numpy as np


def normalize_xrf_v2_wifi(amplitude: np.ndarray, receivers: Optional[Sequence[int]] = None) -> Tuple[np.ndarray, list[int]]:
    """Normalize XRF V2 WiFi amplitude to [time, link, subcarrier].

    The official loader documents each HDF5 sample as `[time, 3, 3, 30]`:
    three receivers, three channels per receiver, and thirty subcarriers.
    Receiver and channel are flattened into a nine-link axis.
    """
    amplitude = np.asarray(amplitude)
    if amplitude.ndim != 4 or amplitude.shape[1:] != (3, 3, 30):
        raise ValueError(f"expected XRF V2 WiFi shape [time,3,3,30], got {amplitude.shape}")
    keep = list(receivers) if receivers is not None else [0, 1, 2]
    if not keep or any(index not in (0, 1, 2) for index in keep):
        raise ValueError("receivers must contain indices from 0, 1, 2")
    selected = amplitude[:, keep, :, :]
    canonical = selected.reshape(selected.shape[0], len(keep) * 3, 30)
    return canonical.astype(np.float32), keep


def convert_xrf_v2_h5(input_path: Path, output_path: Path, receivers: Optional[Sequence[int]] = None) -> Path:
    try:
        import h5py  # type: ignore
    except ImportError as exc:
        raise RuntimeError("XRF V2 conversion requires the optional 'h5py' dependency") from exc
    with h5py.File(input_path, "r") as source:
        amplitude, kept = normalize_xrf_v2_wifi(source["amp"][...], receivers)
        label = source["label"][...]
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path,
        packet_index=np.arange(amplitude.shape[0], dtype=np.int32),
        amplitude=amplitude,
        valid_mask=np.ones(amplitude.shape[0], dtype=bool),
        source_label=label,
    )
    sidecar = {
        "schema_version": "1.0",
        "dataset_id": "xrf-v2",
        "source_file": input_path.name,
        "source_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "source_representation": "processed_amplitude",
        "standard_representation": "amplitude",
        "shape": list(amplitude.shape),
        "axis_order": ["packet", "link", "subcarrier"],
        "sample_rate_hz": None,
        "time_axis": "packet_index",
        "power_unit": "source_amplitude_arbitrary_unit",
        "receivers_kept": kept,
        "transformations": ["select receivers", "flatten receiver and channel into link", "cast float32"],
        "created_at": datetime.now(timezone.utc).isoformat(),
        "tool": "wisensehub-0.5.0"
    }
    sidecar_path = output_path.with_suffix(".json")
    sidecar_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    return sidecar_path
