# Nippur Map Curation Report

- Generated from immutable ODS and shapefile sources.
- Source rows evaluated: 38
- Findspot groups evaluated: 28
- Verified mappings: 18
- Curated mappings: 0
- Unresolved source rows: 10
- Unresolved groups: 7
- Source conflict rows: 7
- Source conflict groups: 3
- Invalid source rows: 0

## Deterministic rule used

`normalize(ODS.area) == normalize(shapefile.Name without leading digits); when area is blank, fall back to normalize(ODS.sector) == normalize(shapefile.Name without leading digits). Historical map plate references (the ODS `map` column) are never used as polygon identifiers.`

Normalization applies Unicode NFKC, trims whitespace, preserves uncertainty markers, and case-folds both sides.

## Human decision required

The remaining rows need scholarly curation because no unique deterministic polygon match exists.

Unresolved area/sector values:

- `EN`: 2
- `EN gen.`: 1
- `IT`: 1
- `Religious Quarter`: 1
- `TA gen.`: 1
- `ZB 4`: 1
