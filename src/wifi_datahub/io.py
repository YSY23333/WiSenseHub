from __future__ import annotations

import csv
import re
from pathlib import Path
from typing import Tuple

import numpy as np


CSI_COLUMN = re.compile(r"^(real|imag|amplitude)_l(\d+)_s(\d+)$")


def load_csi_csv(path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray, str]:
    """Load canonical long-header CSV into time, real, and imaginary arrays.

    Columns are `timestamp_s`, followed by paired `real_l{link}_s{subcarrier}`
    and `imag_l{link}_s{subcarrier}` fields. Amplitude-only inputs are accepted
    but explicitly reported through the returned representation string.
    """
    with path.open("r", encoding="utf-8", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames or "timestamp_s" not in reader.fieldnames:
            raise ValueError("CSV must contain a timestamp_s column")
        rows = list(reader)
        fields = []
        for name in reader.fieldnames:
            match = CSI_COLUMN.match(name)
            if match:
                fields.append((match.group(1), int(match.group(2)), int(match.group(3)), name))
    if not rows:
        raise ValueError("CSV has no data rows")
    links = max(item[1] for item in fields) + 1
    subcarriers = max(item[2] for item in fields) + 1
    timestamp = np.asarray([float(row["timestamp_s"]) for row in rows], dtype=np.float64)
    real = np.zeros((len(rows), links, subcarriers), dtype=np.float32)
    imag = np.zeros_like(real)
    has_complex = any(item[0] == "real" for item in fields) and any(item[0] == "imag" for item in fields)
    if has_complex:
        for component, link, subcarrier, name in fields:
            if component == "real":
                real[:, link, subcarrier] = [float(row[name]) for row in rows]
            elif component == "imag":
                imag[:, link, subcarrier] = [float(row[name]) for row in rows]
        representation = "complex_csi"
    else:
        amplitude_fields = [item for item in fields if item[0] == "amplitude"]
        if not amplitude_fields:
            raise ValueError("CSV needs real/imag pairs or amplitude CSI columns")
        for _, link, subcarrier, name in amplitude_fields:
            real[:, link, subcarrier] = [float(row[name]) for row in rows]
        representation = "amplitude_only"
    return timestamp, real, imag, representation

