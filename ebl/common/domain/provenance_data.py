from pathlib import Path
from typing import Mapping, Optional, Sequence
import json

from ebl.common.domain.provenance_model import GeoCoordinate, ProvenanceRecord


def _load_provenance_data() -> Sequence[dict]:
    data_path = Path(__file__).with_name("provenance_records.json")
    return json.loads(data_path.read_text(encoding="utf-8"))


def build_provenance_records(
    coordinates_map: Optional[Mapping[str, GeoCoordinate]] = None,
) -> Sequence[ProvenanceRecord]:
    coordinates_map = coordinates_map or {}
    return tuple(
        ProvenanceRecord(
            id=record["id"],
            long_name=record["long_name"],
            abbreviation=record["abbreviation"],
            parent=record.get("parent"),
            cigs_key=record.get("cigs_key"),
            sort_key=record.get("sort_key", -1),
            coordinates=coordinates_map.get(record["id"]),
        )
        for record in _load_provenance_data()
    )
