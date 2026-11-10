from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import cast
from unittest.mock import Mock

import pytest

from ebl.fragmentarium.application.findspot_map_data_service import (
    FindspotMapDataService,
    FindspotRepository,
)
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.map_artifact_repository import MapArtifactRepository
from ebl.fragmentarium.domain.findspot import Findspot
from ebl.provenance.domain.provenance_model import ProvenanceRecord
from ebl.tests.fragmentarium.map_data_test_helpers import mapping_record, write_mappings


def make_service(tmp_path: Path, findspots: list[Findspot]) -> FindspotMapDataService:
    write_mappings(
        tmp_path,
        "ASSUR",
        [mapping_record(findspot_id, "assur-a") for findspot_id in range(100, 104)],
    )
    findspot_repository = Mock(spec=FindspotRepository)
    findspot_repository.find_by_ids.return_value = findspots
    fragment_repository = Mock(spec=FragmentRepository)
    fragment_repository.count_fragments_by_findspot_ids.return_value = {100: 3}
    return FindspotMapDataService(
        cast(FindspotRepository, findspot_repository),
        cast(FragmentRepository, fragment_repository),
        MapArtifactRepository(data_dir=tmp_path),
    )


def mapped_findspot(findspot_id: int) -> Findspot:
    return Findspot(findspot_id, ProvenanceRecord("ASSUR", "Assur", "Ass"))


def test_repeated_drift_warns_once_without_changing_rows(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    service = make_service(tmp_path, [mapped_findspot(100)])

    first_result = service.find_map_data()
    repeated_result = service.find_map_data()

    assert first_result == repeated_result
    assert [row.findspot.id_ for row in repeated_result] == [100]
    assert repeated_result[0].accessible_fragment_count == 3
    assert len(caplog.records) == 1
    assert "[101, 102, 103]" in caplog.text


def test_distinct_drift_sets_warn_and_healthy_requests_stay_quiet(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    findspots = [mapped_findspot(100)]
    service = make_service(tmp_path, findspots)
    service.find_map_data()
    findspots.append(mapped_findspot(101))
    service.find_map_data()
    findspots.extend([mapped_findspot(102), mapped_findspot(103)])
    assert len(service.find_map_data()) == 4

    assert len(caplog.records) == 2
    assert "[101, 102, 103]" in caplog.records[0].getMessage()
    assert "[102, 103]" in caplog.records[1].getMessage()


def test_drift_warning_cache_evicts_oldest_set(
    tmp_path: Path,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(
        "ebl.fragmentarium.application.findspot_map_data_service.MAX_REPORTED_DROPPED_SETS",
        2,
    )
    findspots = [mapped_findspot(100)]
    service = make_service(tmp_path, findspots)
    for findspot_id in (101, 102):
        service.find_map_data()
        findspots.append(mapped_findspot(findspot_id))
    service.find_map_data()
    findspots[:] = [mapped_findspot(100), mapped_findspot(101)]
    service.find_map_data()
    assert len(caplog.records) == 3
    findspots[:] = [mapped_findspot(100)]
    service.find_map_data()

    assert len(caplog.records) == 4
    assert caplog.records[0].getMessage() == caplog.records[-1].getMessage()


def test_concurrent_requests_warn_once(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    service = make_service(tmp_path, [mapped_findspot(100)])
    with ThreadPoolExecutor(max_workers=4) as executor:
        results = list(executor.map(lambda _: service.find_map_data(), range(16)))

    assert all([row.findspot.id_ for row in result] == [100] for result in results)
    assert len(caplog.records) == 1
