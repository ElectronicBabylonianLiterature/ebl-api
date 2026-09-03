# Kalḫu Map Curation Report

- Generated from immutable ODS and shapefile sources.
- Verified mappings: 8
- Unresolved rows: 10
- Source conflicts: 0
- Invalid source rows: 0

## Deterministic rule used

`normalize(ODS.area) == normalize(shapefile.Name without leading digits); when area is blank, fall back to normalize(ODS.building) == normalize(shapefile.Name without leading digits)`

Normalization applies Unicode NFKC, trims whitespace, removes `?`, and case-folds both sides.

## Human decision required

The remaining rows need scholarly curation because no unique deterministic polygon match exists.

Unresolved area/building values:

- `<blank>`: 7
- `C 50`: 1
- `Upper fill of trench (d. 13) outside north-west corner of Governor's Palace`: 1
- `ZT4`: 1
