# UT-HAR preparation

The adapter supports the official SenseFi NumPy-payload files (despite their
`.csv` extension) and a convenience NPZ containing `data`/`label`, `x`/`y`, or
`amplitude`/`labels`. The tensor must use an official shape such as
`[sample, 250, 90]`.

```text
data/ut-har/original/UT_HAR/
├── data/X_test.csv
└── label/y_test.csv
```

Run:

```bash
wisensehub prepare ut-har
```

The adapter reshapes the 90 channels into three links and thirty subcarriers.
It does not fabricate complex phase or claim this processed representation is
the original raw CSI.

The official processed test values range below zero, so `amplitude` here means
the upstream model feature tensor rather than non-negative physical magnitude.
Do not derive absolute or relative power from this release.

See [the official-release verification record](../verification/ut-har.md).
