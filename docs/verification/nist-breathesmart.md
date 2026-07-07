# NIST BreatheSmart CSI verification

Verified on 2026-07-07 against one official member of the NIST
`BreatheSmartv2.zip` release. The complete ZIP is 212,364,941 bytes and is not
redistributed. The local verification used HTTP Range requests to read the ZIP
central directory and extract only:

```text
Figure 11 a/BreathingPattern1.tar.gz
```

Source reference:

- <https://data.nist.gov/od/id/mds2-2963>

Extracted member:

```text
BreathingPattern1/BreathingPattern1.csv
BreathingPattern1/total_test_input_shuffled.csv
BreathingPattern1/config0001/config0001.csv
BreathingPattern1/config0001/config0001_csi_imag_log.csv
BreathingPattern1/config0001/config0001_csi_real_log.csv
BreathingPattern1/config0001/config0001_csi_status_log.csv
```

Local extracted tar checksum:

```text
0bda5262824362905626db597d1949b1894f4d43ca9236b23d55dd7c9e413057  BreathingPattern1.tar.gz
```

Command:

```bash
wisensehub prepare nist-breathesmart \
  --data-root data \
  --setting random \
  --force \
  --target-rate 20 \
  --duration 4 \
  --layout link-subcarrier
```

Observed native standardized result:

```text
csi_real      (600, 9, 114)  float32
csi_imag      (600, 9, 114)  float32
amplitude     (600, 9, 114)  float32
timestamp_s   (600,)         float64
packet_index  (600,)         int32
valid_mask    (600,)         bool
config_*      scalar strings copied from config0001.csv
```

Observed derived-view result:

```text
csi_real      (80, 1026)  float32
csi_imag      (80, 1026)  float32
amplitude     (80, 1026)  float32
timestamp_s   (80,)       float64
packet_index  (80,)       int32
valid_mask    (80,)       bool
split          train=1, val=0, test=0
```

The 1026 feature channels come from flattening 9 links × 114 subcarriers. This
verification confirms the official real/imaginary CSV pairing, reshape logic,
configuration metadata preservation, and derived-view path for one official
BreatheSmart experiment member.
