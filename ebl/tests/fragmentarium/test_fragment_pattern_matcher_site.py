from typing import Dict, List, Optional, Sequence

from ebl.fragmentarium.infrastructure.fragment_pattern_matcher import PatternMatcher
from ebl.provenance.domain.provenance_model import ProvenanceRecord

BABYLONIA = ProvenanceRecord(id="BABYLONIA", long_name="Babylonia", abbreviation="Bab")
BABYLON = ProvenanceRecord(
    id="BABYLON", long_name="Babylon", abbreviation="Bbl", parent="Babylonia"
)
MERKES = ProvenanceRecord(
    id="MERKES", long_name="Merkes", abbreviation="Mrk", parent="Babylon"
)
RECORDS = (BABYLONIA, BABYLON, MERKES)


class _StubProvenanceService:
    def __init__(self, records: Sequence[ProvenanceRecord] = RECORDS) -> None:
        self._records = records

    def find_by_name(self, name: str) -> Optional[ProvenanceRecord]:
        return next(
            (record for record in self._records if record.long_name == name), None
        )

    def find_by_id(self, id_: str) -> Optional[ProvenanceRecord]:
        return next((record for record in self._records if record.id == id_), None)

    def find_children(self, long_name: str) -> List[ProvenanceRecord]:
        return [record for record in self._records if record.parent == long_name]


def _site_filter(site: str, service=None) -> Dict:
    matcher = PatternMatcher(
        {"site": site},
        service or _StubProvenanceService(),  # type: ignore[arg-type]
    )
    return matcher._filter_by_site()


def test_an_unknown_site_is_matched_literally() -> None:
    assert _site_filter("Atlantis") == {"archaeology.site": "Atlantis"}


def test_a_site_found_by_id_rather_than_name_is_resolved() -> None:
    assert _site_filter("babylonia") == {"archaeology.site": "Babylonia"}


def test_a_top_level_site_matches_only_itself() -> None:
    assert _site_filter("Babylonia") == {"archaeology.site": "Babylonia"}


def test_a_site_with_children_matches_itself_and_its_children() -> None:
    assert _site_filter("Babylon") == {
        "archaeology.site": {"$in": ["Babylon", "Merkes"]}
    }


def test_a_leaf_site_matches_only_itself() -> None:
    assert _site_filter("Merkes") == {"archaeology.site": "Merkes"}


def test_no_site_in_the_query_adds_no_filter() -> None:
    matcher = PatternMatcher({}, _StubProvenanceService())  # type: ignore[arg-type]

    assert matcher._filter_by_site() == {}
