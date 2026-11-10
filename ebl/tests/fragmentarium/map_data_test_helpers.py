from typing import Sequence
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.provenance.domain.provenance_model import ProvenanceRecord
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber
from pathlib import Path
import json
from ebl.fragmentarium.application.map_artifact_storage import publish_artifact_set
from scripts.maps.map_curated_mappings import CuratedMappingRecord


def mapping_record(findspot_id: int, *polygon_ids: str) -> CuratedMappingRecord:
    return {
        "findspotId": findspot_id,
        "polygonIds": list(polygon_ids),
        "locationPrecision": "excavation-area",
        "matchMethod": "verified-source",
        "source": "Test Tafeln.ods",
        "sourceRevision": "2026-08-05",
    }


def write_mappings(
    data_dir: Path, site_id: str, records: list[CuratedMappingRecord]
) -> None:
    prefix = site_id.lower()
    filename = f"{prefix}_findspot_polygon_mappings.json"
    publish_artifact_set(
        data_dir, prefix, "test-revision", {filename: json.dumps(records)}
    )


def seed_map_fragment(
    fragment_repository: FragmentRepository,
    site: ProvenanceRecord | None,
    findspot_id: int,
    number: str,
    scopes: Sequence[Scope] = (),
) -> None:
    fragment = FragmentFactory.build(
        number=MuseumNumber.of(number),
        archaeology=Archaeology(site=site, findspot_id=findspot_id),
        authorized_scopes=list(scopes),
    )
    fragment_repository.create(fragment)
