from __future__ import annotations

import hashlib
import json
import urllib.request
from pathlib import Path
from typing import Dict, List

from .catalog import repository_root


def load_downloads() -> Dict[str, List[dict]]:
    path = repository_root() / "catalog" / "downloads.json"
    return json.loads(path.read_text(encoding="utf-8"))["downloads"]


def _checksum(path: Path, algorithm: str) -> str:
    digest = hashlib.new(algorithm)
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def download_dataset(dataset_id: str, output_root: Path) -> List[Path]:
    manifests = load_downloads()
    if dataset_id not in manifests:
        raise ValueError(f"{dataset_id} has no direct-download manifest; use its catalog landing page")
    destination = output_root / dataset_id / "original"
    destination.mkdir(parents=True, exist_ok=True)
    written = []
    for item in manifests[dataset_id]:
        target = destination / item["name"]
        print(f"Downloading {item['url']} -> {target}")
        urllib.request.urlretrieve(item["url"], target)
        if item.get("bytes") is not None and target.stat().st_size != item["bytes"]:
            target.unlink(missing_ok=True)
            raise ValueError(f"size mismatch for {item['name']}")
        if item.get("checksum"):
            algorithm, expected = item["checksum"].split(":", 1)
            actual = _checksum(target, algorithm)
            if actual != expected:
                target.unlink(missing_ok=True)
                raise ValueError(f"checksum mismatch for {item['name']}")
        written.append(target)
    receipt = destination / "download-receipt.json"
    receipt.write_text(json.dumps({"dataset_id": dataset_id, "files": [item.name for item in written]}, indent=2) + "\n", encoding="utf-8")
    return written

