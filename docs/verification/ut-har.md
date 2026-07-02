# UT-HAR official-release verification

Verified on 2026-07-02 against the `X_test.csv` and `y_test.csv` members of the
official SenseFi `UT_HAR.zip` release. Only those two ZIP members were fetched
with HTTP range requests; the 383,128,602-byte archive was not redistributed.

Source references:

- <https://github.com/xyanchen/WiFi-CSI-Sensing-Benchmark>
- <https://drive.google.com/drive/folders/1R0R8SlVbLI1iUFQCzh_mH90H_4CW2iwt>

Input checksums:

```text
ff43eec65622f0fb0ed51b812d98192ff6fd5c171369837affa6b2a61f29776e  X_test.csv
cdbabcc758f3797a15554ed3c35b195422a753db04477affe567077d9661dff1  y_test.csv
```

Command:

```bash
wisensehub prepare ut-har --data-root data --setting official --force
```

Observed result:

```text
amplitude       (500, 250, 3, 30)  float32
valid_mask      (500, 250)         bool, 100% valid
activity_label  (500,)             int16, labels 0–6
official split  train=0, val=0, test=500
NaN count       0
```

The standardized NPZ checksum was
`aa39be400cb14d2c0700e441f7999118f06f50165b665f77b4cd10667fb035c4`.
The upstream processed feature values ranged from approximately -9.9005 to
30.5395; they are not interpreted as calibrated physical amplitude or power.
