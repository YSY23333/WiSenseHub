# Changelog

## 0.5.0 — 2026-07-01

- Verified the UT-HAR adapter against the official SenseFi test split and fixed
  the released `X_test.csv` to `y_test.csv` label-pair naming convention.
- Replaced extension-only fallback conversion with per-dataset source discovery
  and dataset-aware adapters for all 25 catalog entries.
- Ported official structures for Intel 5300 binary CSI, Zarr, gzip JSON Lines,
  MATLAB tables/CFR traces, paired real/imaginary CSV, frame directories, and
  task-specific NPY/NPZ releases.
- Added WiFiTAD temporal annotations and prevented the paired WiFi/UWB adapter
  from ingesting UWB CIR files as WiFi CSI.
- Added implementation tiers and official preprocessing/schema references to
  the registry, CLI, documentation, and dataset website.
- Expanded adapter, source-layout, and end-to-end regression coverage.

## 0.4.0 — 2026-07-01

- Registered converters for all 25 catalog datasets, including compressed JSON
  and array-cell CSV support for processed releases.
- Added selectable official, random, cross-subject, cross-environment,
  cross-device, and dataset-specific evaluation settings.
- Added leakage-safe group holdout, deterministic random, predefined,
  trial-order, source-group, and external-JSON split engines.
- Added optional `metadata.csv`/`metadata.jsonl` mappings for opaque releases.
- Added split manifests, CLI setting discovery, website protocol tables, and
  conversion/split regression tests.

## 0.3.0 — 2026-07-01

- Added a unified `wisensehub prepare <dataset-id>` command.
- Standardized the `original/`, `standardized/`, and `reports/` directory flow.
- Added automatic source discovery, batch conversion, skip/force behavior,
  per-output quality reports, and `prepare-manifest.json` diagnostics.
- Added end-to-end prepare tests for Wallhack1.8k and UT-HAR.
- Added per-dataset preparation guides and website commands.

## 0.2.0 — 2026-07-01

- Added ARIL processed-MAT adapter with activity and location labels.
- Added UT-HAR shape adapter for the SenseFi amplitude representation.
- Added XRF V2 HDF5 WiFi adapter based on the official loader dimensions.
- Added NPZ quality reports covering shape, dtype, NaNs, ranges, and validity.
- Added a reproducible pipeline example page to the GitHub Pages site.
- Distinguished `adapter-ready` from `verified` to avoid claiming unexecuted
  conversions as complete.
- Expanded the test suite from four to seven tests.

## 0.1.0 — 2026-06-28

- Initial 18-dataset catalog and 11-task taxonomy.
- Canonical NPZ representation and generic CSV standardization pipeline.
- Wallhack I/Q and subcarrier parser.
- Static catalog website and GitHub Pages workflow.
