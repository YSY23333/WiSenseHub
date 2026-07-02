from __future__ import annotations

import hashlib
import json
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List

import numpy as np


def _signed_byte(value: int) -> int:
    value &= 0xFF
    return value - 256 if value >= 128 else value


def parse_bfee(payload_record: bytes) -> Dict[str, object]:
    """Port of the Intel 5300 CSI Tool read_bfee.c record parser."""
    if len(payload_record) < 20:
        raise ValueError("truncated Intel 5300 beamforming record")
    timestamp_low = int.from_bytes(payload_record[0:4], "little")
    bfee_count = int.from_bytes(payload_record[4:6], "little")
    nrx, ntx = payload_record[8], payload_record[9]
    if nrx not in (1, 2, 3) or ntx not in (1, 2, 3):
        raise ValueError(f"invalid Intel 5300 antenna dimensions ntx={ntx}, nrx={nrx}")
    antenna_sel = payload_record[15]
    declared_len = int.from_bytes(payload_record[16:18], "little")
    expected_len = (30 * (nrx * ntx * 8 * 2 + 3) + 7) // 8
    if declared_len != expected_len:
        raise ValueError(f"beamforming payload length {declared_len} != expected {expected_len}")
    payload = payload_record[20:]
    if len(payload) < expected_len:
        raise ValueError("truncated Intel 5300 CSI bit payload")
    csi = np.empty((ntx, nrx, 30), dtype=np.complex64)
    bit_index = 0
    for subcarrier in range(30):
        bit_index += 3
        remainder = bit_index % 8
        for pair in range(nrx * ntx):
            byte_index = bit_index // 8
            real = (payload[byte_index] >> remainder) | (payload[byte_index + 1] << (8 - remainder))
            imag = (payload[byte_index + 1] >> remainder) | (payload[byte_index + 2] << (8 - remainder))
            tx, rx = pair % ntx, pair // ntx
            csi[tx, rx, subcarrier] = complex(_signed_byte(real), _signed_byte(imag))
            bit_index += 16
    permutation = [antenna_sel & 0x3, (antenna_sel >> 2) & 0x3, (antenna_sel >> 4) & 0x3]
    if nrx > 1 and sum(value + 1 for value in permutation[:nrx]) == (1, 3, 6)[nrx - 1]:
        reordered = np.empty_like(csi)
        for source_rx, destination_rx in enumerate(permutation[:nrx]):
            reordered[:, destination_rx, :] = csi[:, source_rx, :]
        csi = reordered
    return {
        "timestamp_low": timestamp_low, "bfee_count": bfee_count, "nrx": nrx, "ntx": ntx,
        "rssi": [payload_record[10], payload_record[11], payload_record[12]],
        "noise": _signed_byte(payload_record[13]), "agc": payload_record[14], "csi": csi,
    }


def read_bf_file(path: Path) -> List[Dict[str, object]]:
    records: List[Dict[str, object]] = []
    with path.open("rb") as handle:
        while True:
            length_bytes = handle.read(2)
            if not length_bytes:
                break
            if len(length_bytes) != 2:
                raise ValueError("truncated Intel 5300 record length")
            field_len = struct.unpack(">H", length_bytes)[0]
            code = handle.read(1)
            body = handle.read(max(field_len - 1, 0))
            if len(code) != 1 or len(body) != field_len - 1:
                raise ValueError("truncated Intel 5300 record")
            if code[0] == 187:
                records.append(parse_bfee(body))
    if not records:
        raise ValueError("no Intel 5300 beamforming records (code 187) found")
    return records


def convert_wiar_dat(input_path: Path, output_path: Path) -> Path:
    records = read_bf_file(input_path)
    shapes = {np.asarray(record["csi"]).shape for record in records}
    if len(shapes) != 1:
        raise ValueError(f"WiAR antenna configuration changes within file: {sorted(shapes)}")
    csi = np.stack([np.asarray(record["csi"]) for record in records])
    csi = csi.reshape(csi.shape[0], csi.shape[1] * csi.shape[2], 30)
    timestamps = np.asarray([record["timestamp_low"] for record in records], dtype=np.float64)
    timestamps = (timestamps - timestamps[0]) / 1_000_000.0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(
        output_path, timestamp_s=timestamps, csi_real=csi.real.astype(np.float32),
        csi_imag=csi.imag.astype(np.float32), amplitude=np.abs(csi).astype(np.float32),
        rssi=np.asarray([record["rssi"] for record in records], dtype=np.int16),
        noise_db=np.asarray([record["noise"] for record in records], dtype=np.int16),
        agc=np.asarray([record["agc"] for record in records], dtype=np.int16),
        valid_mask=np.ones(csi.shape[0], dtype=bool),
    )
    sidecar = {
        "schema_version": "1.0", "dataset_id": "wiar", "source_file": input_path.name,
        "source_sha256": hashlib.sha256(input_path.read_bytes()).hexdigest(),
        "source_representation": "raw_iq", "standard_representation": "complex_csi",
        "shape": list(csi.shape), "axis_order": ["time", "link", "subcarrier"],
        "sample_rate_hz": 30.0, "time_axis": "timestamp_s", "time_unit": "s",
        "power_unit": "source_csi_arbitrary_unit",
        "transformations": ["port official read_bf_file/read_bfee bit parser", "apply receive-antenna permutation", "flatten tx/rx into link"],
        "created_at": datetime.now(timezone.utc).isoformat(), "tool": "wisensehub-0.5.0",
    }
    sidecar_path = output_path.with_suffix(".json")
    sidecar_path.write_text(json.dumps(sidecar, indent=2) + "\n", encoding="utf-8")
    return sidecar_path
