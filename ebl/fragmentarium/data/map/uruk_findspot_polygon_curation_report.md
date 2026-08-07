# Uruk Map Curation Report

- Generated from immutable ODS and shapefile sources.
- Verified mappings: 131
- Unresolved rows: 12
- Source conflicts: 0
- Invalid source rows: 0

## Deterministic rule used

`normalize(ODS.area) == normalize(shapefile.Name without leading digits)`

Normalization applies Unicode NFKC, trims whitespace, removes `?`, and case-folds both sides.

## Human decision required

The remaining rows need scholarly curation because no unique deterministic polygon match exists.

Unresolved area labels:

- `<blank>`: 7
- `Oc`: 1
- `Pd XVI/1`: 1
- `Pd XVI/4`: 1
- `Pe XV/5`: 1
- `XVIII/1`: 1
