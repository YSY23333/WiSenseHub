from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Iterable, Optional, Sequence

import numpy as np


TIME_AXIS_NAMES = {"time", "packet"}
SIGNAL_ARRAYS = {
    "amplitude", "csi_real", "csi_imag", "phase_rad", "power_db_rel",
    "official_normalized_amplitude", "bvp",
}


@dataclass(frozen=True)
class ViewOptions:
    target_rate_hz: Optional[float] = None
    duration_s: Optional[float] = None
    target_length: Optional[int] = None
    interpolation: str = "linear"
    layout: str = "canonical"
    links: Optional[int] = None
    subcarriers: Optional[int] = None

    def requested(self) -> bool:
        return any((
            self.target_rate_hz is not None,
            self.duration_s is not None,
            self.target_length is not None,
            self.interpolation != "linear",
            self.layout != "canonical",
            self.links is not None,
            self.subcarriers is not None,
        ))


def _load_sidecar(path: Path) -> Dict[str, object]:
    sidecar_path = path.with_suffix(".json")
    if not sidecar_path.exists():
        return {}
    return json.loads(sidecar_path.read_text(encoding="utf-8"))


def _primary_array(files: Iterable[str], sidecar: Dict[str, object]) -> str:
    preferred = sidecar.get("standard_representation")
    if isinstance(preferred, str) and preferred in files:
        return preferred
    for name in ("amplitude", "csi_real", "bvp"):
        if name in files:
            return name
    return next(iter(files))


def _time_axis(axes: Sequence[str], shape: Sequence[int]) -> Optional[int]:
    for index, axis in enumerate(axes):
        if axis in TIME_AXIS_NAMES:
            return index
    if axes and axes[0] == "sample" and len(shape) >= 2:
        return 1
    if len(shape) >= 3:
        return 0
    return None


def _source_rate(sidecar: Dict[str, object], arrays: Dict[str, np.ndarray], time_axis: int) -> Optional[float]:
    value = sidecar.get("sample_rate_hz")
    if isinstance(value, (int, float)) and float(value) > 0:
        return float(value)
    timestamp = arrays.get("timestamp_s")
    if timestamp is not None and timestamp.ndim == 1 and timestamp.size >= 2:
        diffs = np.diff(timestamp.astype(np.float64))
        diffs = diffs[np.isfinite(diffs) & (diffs > 0)]
        if diffs.size:
            return 1.0 / float(np.median(diffs))
    return None


def _target_count(length: int, source_rate_hz: Optional[float], options: ViewOptions) -> int:
    if options.target_length is not None:
        if options.target_length <= 0:
            raise ValueError("target_length must be positive")
        return int(options.target_length)
    rate = options.target_rate_hz if options.target_rate_hz is not None else source_rate_hz
    if options.duration_s is not None:
        if options.duration_s <= 0:
            raise ValueError("duration_s must be positive")
        if rate is None:
            raise ValueError("--duration requires --target-rate, a sidecar sample_rate_hz, or timestamp_s")
        return max(1, int(round(float(options.duration_s) * float(rate))))
    if options.target_rate_hz is not None:
        if source_rate_hz is None:
            raise ValueError("--target-rate requires sidecar sample_rate_hz or timestamp_s")
        return max(1, int(round(length * float(options.target_rate_hz) / float(source_rate_hz))))
    return length


def _nearest_indices(source_count: int, target_count: int) -> np.ndarray:
    if target_count == 1:
        return np.asarray([0], dtype=np.int64)
    positions = np.linspace(0, source_count - 1, target_count)
    return np.rint(positions).astype(np.int64)


def _linear_resample(value: np.ndarray, axis: int, target_count: int) -> np.ndarray:
    source_count = value.shape[axis]
    if source_count == target_count:
        return value.copy()
    if source_count == 1:
        return np.repeat(value, target_count, axis=axis)
    moved = np.moveaxis(value, axis, 0)
    flat = moved.reshape(source_count, -1)
    source_x = np.linspace(0.0, 1.0, source_count)
    target_x = np.linspace(0.0, 1.0, target_count)
    result = np.empty((target_count, flat.shape[1]), dtype=np.float32 if np.issubdtype(value.dtype, np.floating) else value.dtype)
    for column in range(flat.shape[1]):
        result[:, column] = np.interp(target_x, source_x, flat[:, column])
    result = result.reshape((target_count,) + moved.shape[1:])
    return np.moveaxis(result, 0, axis).astype(value.dtype, copy=False)


def _resize_time(value: np.ndarray, axis: int, target_count: int, interpolation: str) -> np.ndarray:
    source_count = value.shape[axis]
    if source_count == target_count:
        return value.copy()
    if interpolation == "none":
        slices = [slice(None)] * value.ndim
        keep = min(source_count, target_count)
        slices[axis] = slice(0, keep)
        cropped = value[tuple(slices)]
        if keep == target_count:
            return cropped.copy()
        pad_width = [(0, 0)] * value.ndim
        pad_width[axis] = (0, target_count - keep)
        return np.pad(cropped, pad_width, mode="constant")
    if interpolation == "nearest" or not np.issubdtype(value.dtype, np.floating):
        return np.take(value, _nearest_indices(source_count, target_count), axis=axis)
    if interpolation == "linear":
        return _linear_resample(value, axis, target_count)
    raise ValueError(f"unsupported interpolation {interpolation!r}; choose none, nearest, or linear")


def _resize_mask(mask: np.ndarray, axis: int, target_count: int, interpolation: str) -> np.ndarray:
    if mask.shape[axis] == target_count:
        return mask.copy()
    if interpolation == "none":
        resized = _resize_time(mask.astype(np.uint8), axis, target_count, "none").astype(bool)
        source_count = mask.shape[axis]
        if target_count > source_count:
            slices = [slice(None)] * resized.ndim
            slices[axis] = slice(source_count, None)
            resized[tuple(slices)] = False
        return resized
    return np.take(mask, _nearest_indices(mask.shape[axis], target_count), axis=axis).astype(bool)


def _reshape_link_subcarrier(value: np.ndarray, axes: Sequence[str], options: ViewOptions) -> tuple[np.ndarray, list[str]]:
    axes = list(axes)
    if options.layout == "canonical":
        return value, axes
    time_axis = _time_axis(axes, value.shape)
    sample_axis = axes.index("sample") if "sample" in axes and len(axes) == value.ndim else None
    keep = [axis for axis in (sample_axis, time_axis) if axis is not None]
    feature_axes = [index for index in range(value.ndim) if index not in keep]
    order = keep + feature_axes
    moved = np.transpose(value, order)
    leading = moved.shape[:len(keep)]
    feature_size = int(np.prod(moved.shape[len(keep):], dtype=np.int64))
    flat = moved.reshape(leading + (feature_size,))
    return flat, [axes[index] for index in keep] + ["feature"]


def create_standard_view(input_path: Path, output_path: Path, options: ViewOptions) -> Path:
    if options.target_rate_hz is not None and options.target_rate_hz <= 0:
        raise ValueError("target_rate_hz must be positive")
    if options.interpolation not in {"none", "nearest", "linear"}:
        raise ValueError("--interpolation must be none, nearest, or linear")
    if options.layout not in {"canonical", "flat", "link-subcarrier"}:
        raise ValueError("--layout must be canonical, flat, or link-subcarrier")
    if not options.requested():
        raise ValueError("no view options were requested")

    sidecar = _load_sidecar(input_path)
    source = np.load(input_path, allow_pickle=False)
    arrays = {name: source[name] for name in source.files}
    primary = _primary_array(arrays.keys(), sidecar)
    axes = list(sidecar.get("axis_order") or [])
    if not axes:
        axes = ["sample", "time", "link", "subcarrier"] if arrays[primary].ndim == 4 else ["time", "link", "subcarrier"]
    time_axis = _time_axis(axes, arrays[primary].shape)
    if time_axis is None:
        raise ValueError(f"cannot identify a time axis for primary array {primary} with axes {axes}")
    source_length = arrays[primary].shape[time_axis]
    if options.links is not None and "link" in axes:
        observed = arrays[primary].shape[axes.index("link")]
        if observed != options.links:
            raise ValueError(f"--links expected {options.links}, but standardized tensor has {observed}")
    if options.subcarriers is not None and "subcarrier" in axes:
        observed = arrays[primary].shape[axes.index("subcarrier")]
        if observed != options.subcarriers:
            raise ValueError(f"--subcarriers expected {options.subcarriers}, but standardized tensor has {observed}")
    source_rate = _source_rate(sidecar, arrays, time_axis)
    target_length = _target_count(source_length, source_rate, options)
    target_rate = options.target_rate_hz if options.target_rate_hz is not None else source_rate

    output_arrays: Dict[str, np.ndarray] = {}
    for name, value in arrays.items():
        value_axes = axes if value.shape == arrays[primary].shape else None
        if name in SIGNAL_ARRAYS and value_axes:
            resized = _resize_time(value, time_axis, target_length, options.interpolation)
            reshaped, new_axes = _reshape_link_subcarrier(resized, value_axes, options)
            output_arrays[name] = reshaped
        elif name == "valid_mask":
            mask_axis = 1 if value.ndim >= 2 and axes and axes[0] == "sample" else 0
            output_arrays[name] = _resize_mask(value.astype(bool), mask_axis, target_length, options.interpolation)
        elif name in {"packet_index", "timestamp_s"} and value.ndim == 1 and value.size == source_length:
            if name == "timestamp_s" and target_rate:
                output_arrays[name] = np.arange(target_length, dtype=np.float64) / float(target_rate)
            elif name == "timestamp_s":
                output_arrays[name] = np.linspace(float(value[0]), float(value[-1]), target_length, dtype=np.float64)
            else:
                output_arrays[name] = np.arange(target_length, dtype=np.int32)
        else:
            output_arrays[name] = value

    primary_value = output_arrays[primary]
    output_axes = _reshape_link_subcarrier(arrays[primary], axes, options)[1] if options.layout != "canonical" else axes
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(output_path, **output_arrays)
    metadata = dict(sidecar)
    transformations = list(metadata.get("transformations") or [])
    transformations.append(
        f"derived view: target_length={target_length}, target_rate_hz={target_rate}, "
        f"interpolation={options.interpolation}, layout={options.layout}"
    )
    metadata.update({
        "schema_version": metadata.get("schema_version", "1.0"),
        "derived_from": str(input_path),
        "standard_representation": primary,
        "shape": list(primary_value.shape),
        "axis_order": output_axes,
        "sample_rate_hz": target_rate,
        "duration_s": (float(target_length) / float(target_rate)) if target_rate else metadata.get("duration_s"),
        "view_options": {
            "target_rate_hz": options.target_rate_hz,
            "duration_s": options.duration_s,
            "target_length": options.target_length,
            "interpolation": options.interpolation,
            "layout": options.layout,
            "links": options.links,
            "subcarriers": options.subcarriers,
        },
        "transformations": transformations,
        "created_at": datetime.now(timezone.utc).isoformat(),
    })
    sidecar_path = output_path.with_suffix(".json")
    sidecar_path.write_text(json.dumps(metadata, indent=2) + "\n", encoding="utf-8")
    return sidecar_path
