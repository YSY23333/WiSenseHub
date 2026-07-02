# Wallhack1.8k preparation

Download and extract the official Zenodo archive so that CSV files remain
under their LoS/NLoS and antenna-system folders:

```text
data/wallhack18k/original/
├── LOS/BQ/*.csv
├── LOS/PIFA/*.csv
├── NLOS/BQ/*.csv
└── NLOS/PIFA/*.csv
```

Run a small trial, then the complete conversion:

```bash
wisensehub prepare wallhack18k --limit 5
wisensehub prepare wallhack18k --force
```

The adapter parses the source `[imaginary, real, ...]` vectors, selects the
documented 52 L-LTF subcarriers, and retains the path-derived scenario.

