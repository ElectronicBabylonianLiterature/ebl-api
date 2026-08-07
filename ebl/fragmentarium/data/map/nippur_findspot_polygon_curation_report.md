# Nippur Map Curation Report

- Generated from immutable ODS and shapefile sources.
- Verified mappings: 20
- Unresolved rows: 8
- Source conflicts: 1
- Invalid source rows: 0

## Deterministic rule used

`normalize(ODS.area) == normalize(shapefile.Name without leading digits); when area is blank, fall back to normalize(ODS.sector) == normalize(shapefile.Name without leading digits). Historical map plate references (the ODS `map` column) are never used as polygon identifiers.`

Normalization applies Unicode NFKC, trims whitespace, removes `?`, and case-folds both sides.

## Human decision required

The remaining rows need scholarly curation because no unique deterministic polygon match exists.

Unresolved area/sector values:

- `<blank>`: 1
- `EN`: 2
- `EN gen.`: 1
- `IT`: 1
- `TA gen.`: 1
- `ZB 4`: 1
