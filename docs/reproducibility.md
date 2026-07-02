# Reproducibility checklist

Every adapter-ready dataset must provide:

- an official landing page and explicit access mode;
- source format and tensor-axis documentation;
- a conversion command that does not require manual code edits;
- source checksum or a download receipt when the host supplies no checksum;
- a standardized sidecar recording every transformation;
- a quality report with shapes, dtypes, NaN counts, ranges, and valid fraction;
- tests using the official source shape and label semantics;
- an honest distinction between complex CSI, amplitude-only data, and derived representations.

`adapter-ready` means the parser and shape tests exist. `verified` is reserved
for an adapter executed successfully against an official downloaded release.
