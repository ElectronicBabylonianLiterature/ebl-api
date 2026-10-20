from __future__ import annotations

from collections import defaultdict
from typing import Any, Callable, Mapping, Sequence

from ebl.provenance.domain.provenance_model import ProvenanceRecord
from scripts.kmz.models import (
    ImportPlan,
    KmlPlacemark,
    ProposedUpdate,
    SkippedRecord,
    _MatchOutcome,
)
from scripts.kmz.names import basic_name_key, is_broad_region_record, normalize_name
from scripts.kmz.proposals import _build_update_candidate


def _classify_record(
    record: ProvenanceRecord,
    backend_basic: Mapping[str, Sequence[ProvenanceRecord]],
    backend_normalized: Mapping[str, Sequence[ProvenanceRecord]],
    kmz_basic: Mapping[str, Sequence[KmlPlacemark]],
    kmz_normalized: Mapping[str, Sequence[KmlPlacemark]],
) -> _MatchOutcome:
    if is_broad_region_record(record):
        return _MatchOutcome(
            skipped=SkippedRecord(record.id, record.long_name, "broad region")
        )

    match = _find_match(
        record, backend_basic, backend_normalized, kmz_basic, kmz_normalized
    )
    tier = match["tier"]
    placemark = match["placemark"]

    if tier == "ambiguous":
        return _MatchOutcome(
            ambiguous=1,
            skipped=SkippedRecord(record.id, record.long_name, "ambiguous match"),
        )
    if placemark is None:
        return _MatchOutcome(
            skipped=SkippedRecord(record.id, record.long_name, "no match")
        )

    proposal, skip = _build_update_candidate(record, placemark, tier)
    if tier == "exact":
        return _MatchOutcome(
            exact_unique=1, proposed=proposal, skipped=skip, matched_placemark=placemark
        )
    return _MatchOutcome(
        normalized_unique=1, review=proposal, skipped=skip, matched_placemark=placemark
    )


def build_import_plan(
    records: Sequence[ProvenanceRecord],
    placemarks: Sequence[KmlPlacemark],
) -> ImportPlan:
    usable_placemarks = tuple(
        placemark for placemark in placemarks if placemark.has_usable_geometry
    )
    backend_basic = _index_records(records, basic_name_key)
    backend_normalized = _index_records(records, normalize_name)
    kmz_basic = _index_placemarks(usable_placemarks, basic_name_key)
    kmz_normalized = _index_placemarks(usable_placemarks, normalize_name)

    proposed_updates: list[ProposedUpdate] = []
    review_candidates: list[ProposedUpdate] = []
    skipped_records: list[SkippedRecord] = []
    exact_unique_matches = 0
    normalized_unique_matches = 0
    ambiguous_matches = 0
    matched_placemark_ids: set[int] = set()

    for record in records:
        outcome = _classify_record(
            record, backend_basic, backend_normalized, kmz_basic, kmz_normalized
        )
        exact_unique_matches += outcome.exact_unique
        normalized_unique_matches += outcome.normalized_unique
        ambiguous_matches += outcome.ambiguous
        if outcome.proposed:
            proposed_updates.append(outcome.proposed)
        if outcome.review:
            review_candidates.append(outcome.review)
        if outcome.skipped:
            skipped_records.append(outcome.skipped)
        if outcome.matched_placemark is not None:
            matched_placemark_ids.add(id(outcome.matched_placemark))

    unmatched_provenance_records = sum(
        1 for skipped in skipped_records if skipped.reason == "no match"
    )
    unmatched_kmz_placemarks = sum(
        1
        for placemark in usable_placemarks
        if id(placemark) not in matched_placemark_ids
    )
    return ImportPlan(
        tuple(proposed_updates),
        tuple(review_candidates),
        tuple(skipped_records),
        exact_unique_matches,
        normalized_unique_matches,
        ambiguous_matches,
        unmatched_provenance_records,
        unmatched_kmz_placemarks,
    )


def _index_records(
    records: Sequence[ProvenanceRecord], key_factory: Callable[[str], str]
) -> dict[str, list[ProvenanceRecord]]:
    index: dict[str, list[ProvenanceRecord]] = defaultdict(list)
    for record in records:
        _append_unique_record(index[key_factory(record.long_name)], record)
    return index


def _index_placemarks(
    placemarks: Sequence[KmlPlacemark], key_factory: Callable[[str], str]
) -> dict[str, list[KmlPlacemark]]:
    index: dict[str, list[KmlPlacemark]] = defaultdict(list)
    for placemark in placemarks:
        for variant in placemark.variants:
            _append_unique_placemark(index[key_factory(variant)], placemark)
    return index


def _append_unique_record(
    records: list[ProvenanceRecord], record: ProvenanceRecord
) -> None:
    if all(existing.id != record.id for existing in records):
        records.append(record)


def _append_unique_placemark(
    placemarks: list[KmlPlacemark], placemark: KmlPlacemark
) -> None:
    if all(existing is not placemark for existing in placemarks):
        placemarks.append(placemark)


def _find_match(
    record: ProvenanceRecord,
    backend_basic: Mapping[str, Sequence[ProvenanceRecord]],
    backend_normalized: Mapping[str, Sequence[ProvenanceRecord]],
    kmz_basic: Mapping[str, Sequence[KmlPlacemark]],
    kmz_normalized: Mapping[str, Sequence[KmlPlacemark]],
) -> dict[str, Any]:
    exact_key = basic_name_key(record.long_name)
    exact_backend = backend_basic.get(exact_key, ())
    exact_kmz = kmz_basic.get(exact_key, ())
    if exact_kmz:
        if len(exact_backend) == 1 and len(exact_kmz) == 1:
            return {"tier": "exact", "placemark": exact_kmz[0]}
        return {"tier": "ambiguous", "placemark": None}

    normalized_key = normalize_name(record.long_name)
    normalized_backend = backend_normalized.get(normalized_key, ())
    normalized_kmz = kmz_normalized.get(normalized_key, ())
    if normalized_kmz:
        if len(normalized_backend) == 1 and len(normalized_kmz) == 1:
            return {"tier": "normalized", "placemark": normalized_kmz[0]}
        return {"tier": "ambiguous", "placemark": None}

    return {"tier": "unmatched", "placemark": None}
