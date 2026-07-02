# ARIL preparation

Download the processed amplitude archive linked by the official ARIL
repository and place both split files here:

```text
data/aril/original/
├── train_data_split_amp.mat
└── test_data_split_amp.mat
```

Run:

```bash
wisensehub prepare aril
```

The adapter expects `train_data`/`test_data`, activity labels, and location
labels inside the MAT files. Output is `[sample, packet, link, subcarrier]`.
Because the processed release does not provide trustworthy packet timestamps,
the standard output preserves packet index instead of inventing seconds.

