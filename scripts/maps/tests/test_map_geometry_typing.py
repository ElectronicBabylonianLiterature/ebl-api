import runpy
import typing

import pytest


@pytest.mark.parametrize(
    "module_name",
    [
        "scripts.maps.map_geometry",
        "scripts.maps.map_source_loader",
    ],
)
def test_geospatial_type_annotations_resolve_with_development_crs(
    module_name: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(typing, "TYPE_CHECKING", True)

    namespace = runpy.run_module(module_name)

    assert namespace["CRS"].from_epsg(4326).to_epsg() == 4326
