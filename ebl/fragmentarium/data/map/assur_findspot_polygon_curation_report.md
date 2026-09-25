# Aššur Map Curation Report

- Generated from immutable ODS and shapefile sources.
- Source rows evaluated: 346
- Findspot groups evaluated: 346
- Verified mappings: 315
- Curated mappings: 0
- Unresolved source rows: 31
- Unresolved groups: 31
- Source conflict rows: 0
- Source conflict groups: 0
- Invalid source rows: 0

## Deterministic rule used

`normalize(ODS.area) == normalize(shapefile.Name without leading digits)`

Normalization applies Unicode NFKC, trims whitespace, preserves uncertainty markers, and case-folds both sides.

## Human decision required

The remaining rows need scholarly curation because no unique deterministic polygon match exists.

Unresolved area labels:

- `<blank>`: 7
- `Wohnquartier`: 16
- `bE4V?`: 1
- `gB4II?`: 1
- `i3? town area`: 1
- `town area`: 5
