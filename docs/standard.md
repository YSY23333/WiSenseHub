# WiSenseHub Standard v1

## Design principles

1. Preserve original complex CSI whenever it exists.
2. Never claim absolute physical power when calibration is unavailable.
3. Make every interpolation, crop, pad, and unit conversion reproducible.
4. Keep continuous TAD/TAL streams continuous; fixed windows are derived views.
5. Record missing packets rather than hiding them.

## Canonical signal arrays

A standardized `.npz` output contains a primary signal tensor, `valid_mask`,
and `packet_index`. For CSI releases the primary tensor is `amplitude`; other
arrays are included when supported by the source:

| Array | Shape | Unit | Description |
|---|---|---|---|
| `timestamp_s` | `[T]` | seconds | Monotonic time, starting at zero |
| `csi_real` | `[T, L, S]` | source-native | Real CSI component |
| `csi_imag` | `[T, L, S]` | source-native | Imaginary CSI component |
| `amplitude` | `[T, L, S]` | linear | `sqrt(real² + imag²)` |
| `power_db_rel` | `[T, L, S]` | dB relative | `10 log10(power / reference_power)` |
| `valid_mask` | `[T]` | boolean | True when supported by an observed packet |
| `packet_index` | `[T]` | index | Original or generated packet position |

Clip collections may add a leading sample axis, producing `[N,T,L,S]` and a
mask of shape `[N,T]`. Processed task representations such as Widar3 BVP retain
their documented axes rather than being mislabeled as raw CSI.

`L` is the flattened transmit-receive link dimension and `S` is subcarrier.
Original antenna dimensions remain in the JSON sidecar.

## Time and sampling

- Default clip profile: 4 seconds at 100 Hz (`T=400`).
- Continuous profile: preserve full duration and resample to 100 Hz when the
  source timestamps support it.
- Vital-sign profile: preserve the raw rate and optionally derive a 20 Hz view.
- Interpolation is performed independently on real and imaginary components.
- Samples outside the observed range are zero padded and marked invalid.

## Power units

Commodity CSI is usually uncalibrated. WiSenseHub therefore uses relative dB
with the median valid power of each sample as the 0 dB reference. Absolute dBm
is only permitted when the source supplies a documented calibration equation
and calibration metadata.

## Labels

Clip tasks store one or more labels in the sidecar. TAD/TAL stores a `segments`
array with `start_seconds`, `end_seconds`, and canonical `label`, plus the
original source label.

## Provenance

Every standardized file has a JSON sidecar recording dataset ID, source file,
source checksum when known, adapter version, target rate, duration policy,
power reference, transformations, and creation timestamp.
