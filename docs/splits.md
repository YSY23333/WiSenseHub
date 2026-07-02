# Dataset split settings

WiSenseHub separates conversion from evaluation protocol. Every `prepare`
command writes standardized NPZ files first, then creates
`data/<dataset-id>/splits/<setting>.json`.

List the available settings and their provenance:

```bash
wisensehub settings widar3
```

Select a protocol:

```bash
wisensehub prepare widar3 --setting random --seed 42
wisensehub prepare widar3 --setting cross_subject --holdout 3
wisensehub prepare wallhack18k --setting cross_device --holdout pifa
```

`official` preserves train/validation/test directories or upstream split JSON.
`paper` denotes a protocol described by the dataset paper or its official
benchmark. `hub` denotes a useful WiSenseHub protocol that is not claimed as an
official result-reproduction setting.

## Group metadata

Cross-subject, cross-device, cross-environment, and related protocols never
randomly mix a group between partitions. The tool first extracts group IDs from
common path forms such as `subject_03/`, `room_2/`, or `device_pifa/`.

If the release uses opaque filenames, create `original/metadata.csv`:

```csv
source_file,subject,environment,device,trial
session_a/clip001.mat,1,lab,pifa,1
session_a/clip002.mat,2,lab,pifa,2
session_b/clip003.mat,3,home,bq,15
```

`source_file` is relative to the dataset's `original/` directory. A JSON Lines
file named `metadata.jsonl` with the same fields is also accepted. The command
stops with an actionable error when required group metadata is unavailable;
it does not infer experimental identities from sample order.

## Manifest contract

The split JSON records the dataset and setting IDs, setting kind, provenance,
seed, ratios, sample count, sample references per partition, group assignments,
and the upstream source URL when one is registered. Batch tensors use references
like `standardized/train.npz::17`; continuous recordings use the NPZ path.
