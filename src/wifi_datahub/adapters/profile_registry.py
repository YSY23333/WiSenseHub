from __future__ import annotations

from pathlib import Path
from typing import Callable, Dict

from .csi_bench import convert as convert_csi_bench
from .csida import convert as convert_csida
from .ehunam import convert as convert_ehunam
from .exposing_csi import convert as convert_exposing_csi
from .figshare_csi_har import convert as convert_figshare_csi_har
from .glasgow_activity_localization import convert as convert_glasgow_activity_localization
from .glasgow_multiuser import convert as convert_glasgow_multiuser
from .mm_fi import convert as convert_mm_fi
from .nist_breathesmart import convert as convert_nist_breathesmart
from .ntu_fi import convert as convert_ntu_fi
from .operanet import convert as convert_operanet
from .signfi import convert as convert_signfi
from .widar3 import convert as convert_widar3
from .wifi_80mhz import convert as convert_wifi_80mhz
from .wifi_presence_movement import convert as convert_wifi_presence_movement
from .wifi_tad import convert as convert_wifi_tad
from .wimans import convert as convert_wimans
from .wipe_fall import convert as convert_wipe_fall
from .wireless_har_wifi_uwb import convert as convert_wireless_har_wifi_uwb
from .xrf55 import convert as convert_xrf55


Adapter = Callable[[Path, Path], Path]


DATASET_ADAPTERS: Dict[str, Adapter] = {
    "csi-bench": convert_csi_bench,
    "csida": convert_csida,
    "ehunam": convert_ehunam,
    "exposing-csi": convert_exposing_csi,
    "figshare-csi-har": convert_figshare_csi_har,
    "glasgow-activity-localization": convert_glasgow_activity_localization,
    "glasgow-multiuser": convert_glasgow_multiuser,
    "mm-fi": convert_mm_fi,
    "nist-breathesmart": convert_nist_breathesmart,
    "ntu-fi": convert_ntu_fi,
    "operanet": convert_operanet,
    "signfi": convert_signfi,
    "widar3": convert_widar3,
    "wifi-80mhz": convert_wifi_80mhz,
    "wifi-presence-movement": convert_wifi_presence_movement,
    "wifi-tad": convert_wifi_tad,
    "wimans": convert_wimans,
    "wipe-fall": convert_wipe_fall,
    "wireless-har-wifi-uwb": convert_wireless_har_wifi_uwb,
    "xrf55": convert_xrf55,
}


def convert_dataset(dataset_id: str, input_path: Path, output_path: Path) -> Path:
    try:
        adapter = DATASET_ADAPTERS[dataset_id]
    except KeyError as exc:
        raise ValueError(f"no dataset-specific profile adapter for {dataset_id}") from exc
    return adapter(input_path, output_path)
