import pytest

from scripts.maps.map_artifact_records import build_verified_record
from scripts.maps.map_findspot_grouping import FindspotGroup
from scripts.maps.map_site_config import SITE_CONFIGS
from scripts.maps.map_source_loader import MapOdsRow


def test_unresolved_group_cannot_become_verified_mapping() -> None:
    group = FindspotGroup(1, (MapOdsRow(1),), frozenset(), True)

    with pytest.raises(ValueError, match="one polygon"):
        build_verified_record(SITE_CONFIGS["ASSUR"], group, "revision-1")
