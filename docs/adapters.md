# Dataset adapter matrix

The normal workflow is the same for every dataset:

```bash
wisensehub settings <dataset-id>
wisensehub prepare <dataset-id> --data-root data --setting <setting>
```

Extract the complete official release into
`data/<dataset-id>/original/`. Source discovery preserves the release's
subdirectories and writes one compressed NPZ tensor and JSON sidecar per
recognized source. `reference-implemented` means the parser follows public
official loading/preprocessing code. `schema-implemented` means it follows the
official release documentation, but no public reference loader was available.
Neither tier means that a gated multi-gigabyte release has been downloaded and
smoke-tested; that stronger claim is recorded separately as `verified` in the
dataset catalog.

| Dataset ID | Tier | Recognized official source |
|---|---|---|
| `aril` | reference | processed split MAT |
| `csi-bench` | reference | supervised MAT/HDF5 |
| `csida` | reference | `csi_data_amp` Zarr arrays |
| `ehunam` | reference | CSI MAT with bandwidth metadata |
| `exposing-csi` | reference | AX-CSI `csi_buff` MAT |
| `figshare-csi-har` | reference | session `data.csv` + `label.csv` |
| `glasgow-activity-localization` | schema | amplitude CSV |
| `glasgow-multiuser` | schema | amplitude CSV |
| `mm-fi` | reference | `wifi-csi/frame*.mat` |
| `nist-breathesmart` | reference | paired real/imaginary CSI CSV |
| `ntu-fi` | reference | `train_amp`/`test_amp` MAT |
| `operanet` | reference | MATLAB table with 270 CSI fields |
| `signfi` | reference | `dataset_*.mat` |
| `ut-har` | reference | SenseFi NPZ/NumPy-payload CSV |
| `wallhack18k` | reference | ESP32 CSI CSV |
| `wiar` | reference | Intel 5300 `.dat` beamforming records |
| `widar3` | reference | SenseFi BVP CSV |
| `wifi-80mhz` | reference | 80 MHz CFR MAT |
| `wifi-presence-movement` | reference | gzip JSON Lines complex CSI |
| `wifi-tad` | reference | `smartwifi` NPY + annotation CSV |
| `wimans` | reference | `wifi_csi/amp` NPY or MAT |
| `wipe-fall` | schema | 51-carrier amplitude CSV |
| `wireless-har-wifi-uwb` | schema | files below `WiFi_CSI/` only |
| `xrf-v2` | reference | WiFi HDF5 sequence |
| `xrf55` | reference | WiFi modality NPY |

The executable patterns and direct evidence URLs live in
[`catalog/adapters.json`](../catalog/adapters.json); this file is explanatory,
not a second registry.
