from __future__ import annotations

import hashlib
import ast
import csv
import gzip
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

import numpy as np

from ..io import load_csi_csv


DATA_KEYS = ("csi", "CSI", "amp", "amplitude", "data", "x", "input")
REAL_KEYS = ("csi_real", "real", "real_csi")
IMAG_KEYS = ("csi_imag", "imag", "imag_csi")
LABEL_KEYS = ("label", "labels", "y", "activity_label", "target")
METADATA_KEYS = {
    "subject": ("subject", "subject_id", "person", "person_id", "user", "user_id", "participant"),
    "environment": ("environment", "environment_id", "env", "room", "scene"),
    "device": ("device", "device_id", "receiver", "receiver_id", "rx"),
    "location": ("location", "location_id", "position", "position_id"),
    "orientation": ("orientation", "orientation_id", "angle"),
    "day": ("day", "date", "session"),
    "trial": ("trial", "trial_id", "repetition", "repeat", "rep"),
    "occupancy": ("occupancy", "people_count", "person_count"),
    "experiment": ("experiment", "experiment_id", "exp"),
    "band": ("band", "frequency_band"),
}
ALL_METADATA_KEYS = tuple(key for aliases in METADATA_KEYS.values() for key in aliases)


def _choose(mapping: Dict[str, Any], candidates: tuple[str, ...]) -> Optional[str]:
    return next((key for key in candidates if key in mapping), None)


def _load_h5(path: Path) -> Dict[str, np.ndarray]:
    try:
        import h5py  # type: ignore
    except ImportError as exc:
        raise RuntimeError("HDF5 input requires the optional 'h5py' dependency") from exc
    result: Dict[str, np.ndarray] = {}
    with h5py.File(path, "r") as handle:
        def visit(name, obj):
            if hasattr(obj, "shape") and name.split("/")[-1] in DATA_KEYS + REAL_KEYS + IMAG_KEYS + LABEL_KEYS + ALL_METADATA_KEYS:
                result[name.split("/")[-1]] = obj[...]
        handle.visititems(visit)
    return result


def _load_mat(path: Path) -> Dict[str, np.ndarray]:
    try:
        from scipy.io import loadmat  # type: ignore
    except ImportError as exc:
        raise RuntimeError("MAT input requires the optional 'scipy' dependency") from exc
    return {key: value for key, value in loadmat(path).items() if not key.startswith("__")}


def _load_zarr(path: Path) -> Dict[str, np.ndarray]:
    try:
        import zarr  # type: ignore
    except ImportError as exc:
        raise RuntimeError("Zarr input requires the optional 'zarr' dependency") from exc
    root = zarr.open(str(path), mode="r")
    if hasattr(root, "shape"):
        return {"data": np.asarray(root)}
    result: Dict[str, np.ndarray] = {}
    for key in root.array_keys():
        if key in DATA_KEYS + REAL_KEYS + IMAG_KEYS + LABEL_KEYS + ALL_METADATA_KEYS:
            result[key] = np.asarray(root[key])
    return result


def load_generic_source(path: Path) -> Tuple[Dict[str, np.ndarray], str]:
    suffix = path.suffix.lower()
    if suffix == ".npz":
        source = np.load(path, allow_pickle=False)
        return {key: source[key] for key in source.files}, "npz"
    if suffix == ".npy":
        return {"data": np.load(path, allow_pickle=False)}, "npy"
    if suffix in {".h5", ".hdf5"}:
        return _load_h5(path), "hdf5"
    if suffix == ".mat":
        return _load_mat(path), "mat"
    if suffix == ".zarr" or path.name.endswith(".zarr"):
        return _load_zarr(path), "zarr"
    if suffix == ".csv":
        try:
            timestamp, real, imag, representation = load_csi_csv(path)
            return {"timestamp_s": timestamp, "csi_real": real, "csi_imag": imag}, representation
        except (ValueError, StopIteration):
            with path.open(newline="", encoding="utf-8", errors="ignore") as handle:
                rows = list(csv.DictReader(handle))
            if rows:
                data_column = next((key for key in DATA_KEYS if key in rows[0]), None)
                label_column = next((key for key in LABEL_KEYS if key in rows[0]), None)
                if data_column:
                    parsed = [np.asarray(ast.literal_eval(row[data_column])) for row in rows]
                    result = {"data": np.stack(parsed)}
                    if label_column:
                        result["label"] = np.asarray([row[label_column] for row in rows])
                    return result, "csv_array_cells"
            numeric = np.genfromtxt(path, delimiter=",", skip_header=1)
            if numeric.ndim == 1:
                numeric = numeric[:, None]
            numeric = numeric[:, ~np.all(np.isnan(numeric), axis=0)]
            return {"data": numeric}, "csv_numeric"
    if suffix == ".json" or path.name.endswith(".json.gz"):
        opener = gzip.open if path.name.endswith(".gz") else open
        with opener(path, "rt", encoding="utf-8") as handle:
            text = handle.read()
        try:
            payload = json.loads(text)
        except json.JSONDecodeError:
            payload = [json.loads(line) for line in text.splitlines() if line.strip()]
        if isinstance(payload, dict):
            return {key: np.asarray(value) for key, value in payload.items() if key in DATA_KEYS + REAL_KEYS + IMAG_KEYS + LABEL_KEYS + ALL_METADATA_KEYS}, "json"
        if isinstance(payload, list) and payload and isinstance(payload[0], dict):
            key = next((name for name in DATA_KEYS if name in payload[0]), None)
            if key:
                result = {"data": np.asarray([row[key] for row in payload])}
                label = next((name for name in LABEL_KEYS if name in payload[0]), None)
                if label:
                    result["label"] = np.asarray([row[label] for row in payload])
                return result, "json_records"
        return {"data": np.asarray(payload)}, "json"
    raise ValueError(f"unsupported generic source format: {path}")


def canonicalize_array(array: np.ndarray) -> Tuple[np.ndarray, list[str]]:
    """Conservatively map an array to [..., time, link, subcarrier]."""
    array = np.asarray(array)
    if array.ndim == 1:
        return array[:, None, None], ["time", "link", "subcarrier"]
    if array.ndim == 2:
        return array[:, None, :], ["time", "link", "subcarrier"]
    if array.ndim == 3:
        return array, ["time", "link", "subcarrier"]
    if array.ndim == 4:
        return array, ["sample", "time", "link", "subcarrier"]
    raise ValueError(f"generic adapter supports 1-D to 4-D arrays, got {array.shape}")


def convert_generic(input_path: Path, output_path: Path, dataset_id: str) -> Path:
    source, source_format = load_generic_source(input_path)
    real_key, imag_key = _choose(source, REAL_KEYS), _choose(source, IMAG_KEYS)
    data_key = _choose(source, DATA_KEYS)
    label_key = _choose(source, LABEL_KEYS)
    output: Dict[str, np.ndarray] = {}
    if real_key and imag_key:
        real, axes = canonicalize_array(source[real_key])
        imag, axes_imag = canonicalize_array(source[imag_key])
        if real.shape != imag.shape or axes != axes_imag:
            raise ValueError("real and imaginary CSI shapes differ")
        amplitude = np.hypot(real, imag).astype(np.float32)
        output.update(csi_real=real.astype(np.float32), csi_imag=imag.astype(np.float32), amplitude=amplitude)
        representation = "complex_csi"
    elif data_key:
        raw = np.asarray(source[data_key])
        canonical, axes = canonicalize_array(raw)
        if np.iscomplexobj(canonical):
            output.update(csi_real=canonical.real.astype(np.float32), csi_imag=canonical.imag.astype(np.float32), amplitude=np.abs(canonical).astype(np.float32))
            representation = "complex_csi"
        else:
            output["amplitude"] = canonical.astype(np.float32)
            representation = "processed_amplitude"
    else:
        raise ValueError(f"could not find CSI arrays; available keys: {sorted(source)}")
    time_length = output["amplitude"].shape[1] if axes[0] == "sample" else output["amplitude"].shape[0]
    sample_shape = output["amplitude"].shape[:2] if axes[0] == "sample" else (time_length,)
    output["packet_index"] = np.arange(time_length, dtype=np.int32)
    output["valid_mask"] = np.ones(sample_shape, dtype=bool)
    if label_key:
        output["source_label"] = np.asarray(source[label_key])
    sample_count = output["amplitude"].shape[0] if axes[0] == "sample" else None
    for standard_key, aliases in METADATA_KEYS.items():
        source_key = _choose(source, aliases)
        if source_key:
            values = np.asarray(source[source_key]).reshape(-1)
            if sample_count is None or values.size == sample_count:
                output[standard_key] = values
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, **output)
    sidecar = {
        "schema_version": "1.0", "dataset_id": dataset_id, "source_file": input_path.name,
        "source_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest() if input_path.is_file() else None,
        "source_representation": representation, "source_format": source_format,
        "standard_representation": "complex_csi" if "csi_real" in output else "amplitude",
        "shape": list(output["amplitude"].shape), "axis_order": axes,
        "sample_rate_hz": None, "time_axis": "packet_index", "power_unit": "source_amplitude_arbitrary_unit",
        "transformations": ["canonicalize to sample/time/link/subcarrier", "cast float32"],
        "created_at": datetime.now(timezone.utc).isoformat(), "tool": "wisensehub-0.5.0",
        "warning": "Generic adapter preserves values and axes conservatively; dataset-specific calibration is not inferred."
    }
    sidecar_path = output_path.with_suffix(".json")
    sidecar_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    return sidecar_path
