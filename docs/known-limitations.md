# Known limitations and verification status

WiSenseHub is designed to be honest about what has been verified and what has
only been adapted from public documentation or official preprocessing code.

## Adapter maturity

- `verified`: converted against at least one official release sample in this
  repository's local verification workflow. UT-HAR is currently verified with
  the official SenseFi `X_test/y_test` pair.
- `reference-implemented`: implemented from an official loader, model data
  class, preprocessing script, or dataset paper/code reference, with synthetic
  regression tests matching the documented layout.
- `schema-implemented`: implemented from the released file schema and README
  when no public preprocessing implementation was available.

## Data access and redistribution

Many WiFi sensing datasets are account-gated, application-gated, or unclear
about redistribution. WiSenseHub therefore does not redistribute restricted
data. Users should download the official release, keep the original directory
tree intact, and run `wisensehub prepare`.

## Signal semantics

The hub never invents missing physical meaning:

- amplitude-only releases remain amplitude-only;
- processed BVP or normalized feature tensors are not relabeled as raw CSI;
- relative dB is used only when a reproducible reference can be computed;
- absolute dBm is used only if the source documents calibration metadata.

## Cross-dataset comparability

Fixed-rate and fixed-length derived views are useful for model input, but they
do not make every dataset experimentally equivalent. Hardware, bandwidth,
subcarrier count, subject protocol, environment, and labels still differ and
remain visible in the catalog metadata and sidecars.
