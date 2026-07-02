# UT-HAR preparation

The currently supported input is a processed NPZ containing either
`data`/`label`, `x`/`y`, or `amplitude`/`labels`. The data tensor must use an
official SenseFi-compatible shape such as `[sample, 250, 90]`.

```text
data/ut-har/original/processed.npz
```

Run:

```bash
wisensehub prepare ut-har
```

The adapter reshapes the 90 channels into three links and thirty subcarriers.
It does not fabricate complex phase or claim this processed representation is
the original raw CSI.

