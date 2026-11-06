from pathlib import Path
from typing import cast

import attr
import falcon
from falcon import testing
import pytest

import ebl.app
from ebl.context import Context
from ebl.fragmentarium.application.findspot_map_data_schema import FindspotMapDataSchema
from ebl.fragmentarium.application.findspot_map_data_service import FindspotMapData
from ebl.fragmentarium.application.map_artifact_repository import MapArtifactRepository
from ebl.tests.factories.archaeology import FindspotFactory
from ebl.tests.fragmentarium.map_data_test_helpers import write_mappings


def _client(context: Context, directory: Path) -> testing.TestClient:
    configured = attr.evolve(
        context, map_artifact_repository=MapArtifactRepository(directory)
    )
    return testing.TestClient(ebl.app.create_app(configured))


def test_published_empty_mappings_are_valid_zero_data(
    tmp_path: Path, context: Context
) -> None:
    write_mappings(tmp_path, "ASSUR", [])

    response = cast(
        testing.Result,
        _client(context, tmp_path).simulate_get("/findspots/map-data?site=ASSUR"),
    )

    assert response.status == falcon.HTTP_OK
    assert response.json == {"findspots": []}


@pytest.mark.parametrize(
    "parameter", ["site", "scriptPeriod", "scriptPeriodModifier", "genre"]
)
def test_map_data_rejects_repeated_filter_parameters(
    tmp_path: Path, context: Context, parameter: str
) -> None:
    response = cast(
        testing.Result,
        _client(context, tmp_path).simulate_get(
            f"/findspots/map-data?{parameter}=one&{parameter}=two"
        ),
    )

    assert response.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_one_invalid_site_does_not_break_independent_valid_site_requests(
    tmp_path: Path, context: Context
) -> None:
    write_mappings(tmp_path, "ASSUR", [])
    write_mappings(tmp_path, "URUK", [])
    (tmp_path / "uruk_findspot_polygon_mappings.json").write_text(
        "tampered", encoding="utf-8"
    )
    client = _client(context, tmp_path)

    available = cast(
        testing.Result, client.simulate_get("/findspots/map-data?site=ASSUR")
    )
    unavailable = cast(
        testing.Result, client.simulate_get("/findspots/map-data?site=URUK")
    )

    assert available.status == falcon.HTTP_OK
    assert available.json == {"findspots": []}
    assert unavailable.status == falcon.HTTP_INTERNAL_SERVER_ERROR


def test_map_data_never_serializes_an_unvalidated_location_as_empty_geometry() -> None:
    row = FindspotMapData(FindspotFactory.build(map_location=None), "ASSUR", "Aššur", 0)

    with pytest.raises(ValueError, match="validated map location"):
        FindspotMapDataSchema().dump(row)
