from pathlib import Path

import pytest

from ebl.fragmentarium.application import map_artifact_repository
from ebl.fragmentarium.application.map_artifact_repository import MapArtifactRepository
from ebl.tests.fragmentarium.map_data_test_helpers import mapping_record, write_mappings


def test_immutable_validated_mappings_are_cached_without_exposing_mutable_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    write_mappings(tmp_path, "ASSUR", [mapping_record(100, "assur-a")])
    repository = MapArtifactRepository(tmp_path)
    first = repository.load_site_map_locations("ASSUR")
    expected = dict(first)
    first.clear()

    def reject_repeated_validation(*args: object, **kwargs: object) -> str:
        raise AssertionError("immutable package data must validate once")

    monkeypatch.setattr(
        map_artifact_repository, "read_validated_artifact", reject_repeated_validation
    )

    assert repository.load_site_map_locations("ASSUR") == expected
