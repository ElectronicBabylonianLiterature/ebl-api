# Aššur Map Curation Report

- Generated from immutable ODS and shapefile sources.
- Verified mappings: 304
- Unresolved rows: 42
- Source conflicts: 0
- Invalid source rows: 0

## Deterministic rule used

`normalize(ODS.area) == normalize(shapefile.Name without leading digits)`

Normalization applies Unicode NFKC, trims whitespace, removes `?`, and case-folds both sides.

## Human decision required

The remaining rows need scholarly curation because no unique deterministic polygon match exists.

Unresolved area labels:

- `<blank>`: 7
- `Wohnquartier`: 16
- `bB6I`: 13
- `i3? town area`: 1
- `town area`: 5
