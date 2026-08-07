from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass

from ebl.fragmentarium.application.map_geometry import strict_zip
from ebl.fragmentarium.application.map_mapping_rules import DerivationRecord
from ebl.fragmentarium.application.map_source_loader import MapOdsRow


@dataclass(frozen=True)
class FindspotGroup:
    findspot_id: int
    rows: tuple[MapOdsRow, ...]
    resolved_polygon_ids: frozenset[str]

    @property
    def status(self) -> str:
        if len(self.resolved_polygon_ids) == 1:
            return "resolved"
        if len(self.resolved_polygon_ids) > 1:
            return "conflict"
        return "unresolved"

    @property
    def polygon_id(self) -> str | None:
        return (
            next(iter(self.resolved_polygon_ids)) if self.status == "resolved" else None
        )

    @property
    def representative_row(self) -> MapOdsRow:
        return max(
            self.rows,
            key=lambda row: sum(bool(v) for v in (row.area, row.sector, row.building)),
        )


def group_findspots(
    rows: tuple[MapOdsRow, ...], derivations: tuple[DerivationRecord, ...]
) -> tuple[FindspotGroup, ...]:
    grouped: dict[int, list[MapOdsRow]] = defaultdict(list)
    resolved: dict[int, set[str]] = defaultdict(set)
    order: list[int] = []
    for row, record in strict_zip(rows, derivations):
        if row.findspot_id not in grouped:
            order.append(row.findspot_id)
        grouped[row.findspot_id].append(row)
        if record.status == "verified-mapped" and record.polygon_id is not None:
            resolved[row.findspot_id].add(record.polygon_id)
    return tuple(
        FindspotGroup(
            findspot_id=findspot_id,
            rows=tuple(grouped[findspot_id]),
            resolved_polygon_ids=frozenset(resolved.get(findspot_id, ())),
        )
        for findspot_id in order
    )
