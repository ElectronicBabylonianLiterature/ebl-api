# Kalḫu Map Curation Report

- Generated from immutable ODS and shapefile sources.
- Source rows evaluated: 24
- Findspot groups evaluated: 18
- Verified mappings: 7
- Curated mappings: 0
- Unresolved source rows: 11
- Unresolved groups: 10
- Source conflict rows: 2
- Source conflict groups: 1
- Invalid source rows: 0

## Deterministic rule used

`normalize(ODS.area) == normalize(shapefile.Name without leading digits); when area is blank, fall back to normalize(ODS.building) == normalize(shapefile.Name without leading digits)`

Normalization applies Unicode NFKC, trims whitespace, preserves uncertainty markers, and case-folds both sides.

## Human decision required

The remaining rows need scholarly curation because no unique deterministic polygon match exists.

Unresolved area/building values:

- `A 50`: 1
- `AS 411`: 1
- `B 50`: 1
- `C 50`: 1
- `Governor's Palace`: 1
- `Nabu Temple`: 1
- `South-East Palace`: 1
- `South-West Palace but probably originating in Central Palace`: 1
- `Upper fill of trench (d. 13) outside north-west corner of Governor's Palace`: 1
- `ZT4`: 1
