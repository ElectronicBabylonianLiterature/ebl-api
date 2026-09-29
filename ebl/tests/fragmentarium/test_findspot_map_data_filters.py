import attr
import pytest
from falcon import testing

import ebl.app
from ebl.common.domain.period import Period, PeriodModifier
from ebl.fragmentarium.application.map_artifact_repository import (
    MapArtifactRepository,
)
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.fragmentarium.domain.fragment import Genre, Script
from ebl.tests.factories.archaeology import FindspotFactory
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.map_data_test_helpers import (
    mapping_record,
    write_mappings,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


@pytest.fixture
def map_data_with_script_and_genre(
    tmp_path,
    context,
    findspot_repository,
    fragment_repository,
    seeded_provenance_service,
):
    assur = seeded_provenance_service.find_by_id("ASSUR")
    write_mappings(tmp_path, "ASSUR", [mapping_record(200, "assur-c")])
    findspot_repository.create(FindspotFactory.build(id_=200, site=assur))

    fragment_repository.create(
        FragmentFactory.build(
            number=MuseumNumber.of("X.200"),
            archaeology=Archaeology(site=assur, findspot_id=200),
            script=Script(Period.OLD_BABYLONIAN, PeriodModifier.NONE),
            genres=(Genre(["ARCHIVAL", "Administrative"], False),),
        )
    )
    fragment_repository.create(
        FragmentFactory.build(
            number=MuseumNumber.of("X.201"),
            archaeology=Archaeology(site=assur, findspot_id=200),
            script=Script(Period.NEO_ASSYRIAN, PeriodModifier.NONE),
            genres=(Genre(["CANONICAL", "Catalogues"], False),),
        )
    )

    test_context = attr.evolve(
        context, map_artifact_repository=MapArtifactRepository(data_dir=tmp_path)
    )
    return testing.TestClient(ebl.app.create_app(test_context))


def _count_for(client, query):
    response = client.simulate_get(f"/findspots/map-data{query}")
    return response.json["findspots"][0]["accessibleFragmentCount"]


def test_map_data_script_filter(map_data_with_script_and_genre):
    client = map_data_with_script_and_genre

    assert _count_for(client, "") == 2
    assert _count_for(client, "?scriptPeriod=Old Babylonian") == 1
    assert _count_for(client, "?scriptPeriod=Neo-Assyrian") == 1


def test_map_data_genre_filter(map_data_with_script_and_genre):
    client = map_data_with_script_and_genre

    assert _count_for(client, "?genre=ARCHIVAL:Administrative") == 1
    assert _count_for(client, "?genre=CANONICAL:Catalogues") == 1


def test_map_data_combined_script_and_genre_filter(map_data_with_script_and_genre):
    client = map_data_with_script_and_genre

    assert (
        _count_for(client, "?scriptPeriod=Old Babylonian&genre=ARCHIVAL:Administrative")
        == 1
    )
    assert (
        _count_for(client, "?scriptPeriod=Neo-Assyrian&genre=ARCHIVAL:Administrative")
        == 0
    )


@pytest.mark.parametrize(
    "query",
    [
        "?scriptPeriod=not-a-period",
        "?scriptPeriodModifier=not-a-modifier",
        "?genre=ARCHIVAL:not-a-genre",
    ],
)
def test_map_data_rejects_invalid_filters(map_data_with_script_and_genre, query):
    response = map_data_with_script_and_genre.simulate_get(
        f"/findspots/map-data{query}"
    )

    assert response.status_code == 422
