# WiFi CSI and RSS Presence/Movement verification

Verified on 2026-07-07 against a byte-prefix sample of the official Zenodo
`G19-10.csi.json.gz` CSI file. The full file is 1,375,648,646 bytes and is not
redistributed. The local verification fetched an HTTP Range prefix, decoded the
first 50 valid JSON CSI records, and recompressed those records as a small local
sample under `data/`, which is ignored by git.

Source reference:

- <https://zenodo.org/records/3676058>

Official file metadata from Zenodo:

```text
G19-10.csi.json.gz
size: 1,375,648,646 bytes
md5: ef15ba6f1234a1cbcc8cc749877822bc
```

Local prefix/sample checksums:

```text
25f8f295bdb6c583e7e28167e06c16bad85ba71bf78eba3eeff59c2d1f9c2e89  G19-10.prefix.gz
a2074844c6265fba93c78b71a8759dfb445d54af1deb3baadb6293e360a77817  G19-10.csi.prefix.json.gz
```

Command:

```bash
wisensehub prepare wifi-presence-movement \
  --data-root data \
  --setting random \
  --force \
  --target-rate 100 \
  --duration 1 \
  --layout link-subcarrier
```

Observed derived-view result:

```text
csi_real      (100, 90)  float32
csi_imag      (100, 90)  float32
amplitude     (100, 90)  float32
timestamp_s   (100,)     float64
packet_index  (100,)     int32
valid_mask    (100,)     bool
split          train=1, val=0, test=0
```

The 90 feature channels come from flattening the native `[link, subcarrier]`
axes of 3 links × 30 subcarriers. This verification confirms the official JSON
CSI parser and derived-view path, but it does not claim exhaustive conversion
of every multi-GB Zenodo CSI file.
