# Uruk Map Curation Report

- Generated from immutable ODS and shapefile sources.
- Source rows evaluated: 180
- Findspot groups evaluated: 143
- Verified mappings: 129
- Curated mappings: 0
- Unresolved source rows: 16
- Unresolved groups: 13
- Source conflict rows: 3
- Source conflict groups: 1
- Invalid source rows: 0

## Deterministic rule used

`normalize(ODS.area) == normalize(shapefile.Name without leading digits)`

Normalization applies Unicode NFKC, trims whitespace, preserves uncertainty markers, and case-folds both sides.

## Human decision required

The remaining rows need scholarly curation because no unique deterministic polygon match exists.

Unresolved area labels:

- `<blank>`: 7
- `Oc`: 1
- `Pd XVI/1`: 1
- `Pd XVI/4`: 1
- `Pe XV/5`: 1
- `Ue XVIII/1`: 1
- `XVIII/1`: 1
