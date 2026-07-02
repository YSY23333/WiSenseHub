# XRF V2 preparation

Install data dependencies, download the official XRF V2 release, and place
WiFi HDF5 sequences anywhere below:

```text
data/xrf-v2/original/**/*.h5
```

Run:

```bash
pip install -e ".[data]"
wisensehub prepare xrf-v2 --limit 5
wisensehub prepare xrf-v2 --force
```

The official loader documents WiFi amplitude as `[time, 3, 3, 30]`. The
adapter flattens receiver and channel into nine links, producing
`[time, 9, 30]`, and preserves the source label data.

