import json
from pathlib import Path

import attr
import pytest

from ebl.provenance.domain.provenance_model import GeoCoordinate
from ebl.tests.provenance.kmz_test_helpers import (
    POINT_XML,
    POLYGON_XML,
    placemark,
    record,
)
from scripts import import_kmz_coordinates as cli
from scripts.kmz.proposals import _build_update_candidate


def test_exact_normalized_ambiguous_and_unmatched_plans() -> None:
    exact = record()
    marks = (
        placemark(),
        placemark("Uruk"),
        placemark("Kalhu"),
        placemark("Kalhu"),
        placemark("Unclaimed"),
    )
    plan = cli.build_import_plan(
        (
            exact,
            exact,
            record("Urúk", "URUK"),
            record("Kalhu", "KALHU"),
            record("Sumer", "SUMER"),
            record("Missing", "MISSING"),
        ),
        marks,
    )
    assert plan.exact_unique_matches == 2
    assert plan.normalized_unique_matches == 1
    assert plan.ambiguous_matches == 1
    assert plan.unmatched_provenance_records == 1
    assert plan.unmatched_kmz_placemarks == 3
    assert plan.review_candidates[0].provenance_id == "URUK"
    assert {skipped.reason for skipped in plan.skipped_records} == {
        "ambiguous match",
        "broad region",
        "no match",
    }


def test_normalized_ambiguity_and_duplicate_aliases() -> None:
    plan = cli.build_import_plan(
        (record("Aššur"),), (placemark("Assur / Assur?"), placemark("Assur"))
    )
    assert plan.ambiguous_matches == 1
    assert not plan.proposed_updates


def test_existing_fields_are_preserved() -> None:
    existing = attr.evolve(
        record(),
        coordinates=GeoCoordinate(35, 43),
        polygon_coordinates=(GeoCoordinate(35, 43),),
    )
    plan = cli.build_import_plan(
        (existing,), (placemark(geometry=POINT_XML + POLYGON_XML),)
    )
    assert not plan.proposed_updates
    assert "already has coordinates" in plan.skipped_records[0].reason
    assert "already has polygonCoordinates" in plan.skipped_records[0].reason
    proposal, skipped = _build_update_candidate(
        record(), placemark(geometry=""), "exact"
    )
    assert proposal is None
    assert skipped is not None and skipped.reason == "KMZ has no usable coordinates"


def test_field_allowlist_promotes_only_explicit_normalized_matches() -> None:
    plan = cli.build_import_plan(
        (record(), record("Urúk", "URUK"), record("Kalḫu", "KALHU")),
        (placemark(), placemark("Uruk"), placemark("Kalhu")),
    )
    assert cli.filter_plan_by_allowlist(plan, None) is plan
    filtered = cli.filter_plan_by_allowlist(
        plan, {"URUK": {"coordinates"}, "KALHU": None}
    )
    assert [update.provenance_id for update in filtered.proposed_updates] == ["URUK"]
    assert [update.provenance_id for update in filtered.review_candidates] == ["KALHU"]
    assert filtered.skipped_records[0].reason == "not in allowlist"
    denied = cli.filter_plan_by_allowlist(plan, {"ASSUR": {"polygonCoordinates"}})
    assert not denied.proposed_updates and not denied.review_candidates


def test_allowlist_formats(tmp_path: Path) -> None:
    assert cli.load_allowlist(None) is None
    path = tmp_path / "allowlist.json"
    path.write_text(
        json.dumps({"updates": ["ASSUR", {"_id": "URUK", "fields": ["coordinates"]}]})
    )
    assert cli.load_allowlist(path) == {"ASSUR": None, "URUK": {"coordinates"}}


@pytest.mark.parametrize("payload", [{"updates": 1}, [1], [{"id": 1}]])
def test_invalid_allowlists(tmp_path: Path, payload: object) -> None:
    path = tmp_path / "allowlist.json"
    path.write_text(json.dumps(payload))
    with pytest.raises(ValueError):
        cli.load_allowlist(path)
