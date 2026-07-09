from datetime import date, timedelta

import falcon
import pytest

from ebl.common.domain.period import Period, PeriodModifier
from ebl.common.domain.project import ResearchProject
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.domain.fragment import Script
from ebl.fragmentarium.domain.museum import Museum
from ebl.fragmentarium.domain.record import RecordType
from ebl.fragmentarium.infrastructure.queries import (
    LATEST_TRANSLITERATION_LIMIT,
    LATEST_TRANSLITERATION_LINE_LIMIT,
)
from ebl.tests.factories.fragment import FragmentFactory, TransliteratedFragmentFactory
from ebl.tests.factories.record import RecordEntryFactory, RecordFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import (
    get_provenance_record,
    query_item_of,
    query_result_of,
    query_summary_of,
)


def test_search_with_scopes(client, guest_client, fragmentarium):
    fragment = FragmentFactory.build(
        authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS]
    )
    fragmentarium.create(fragment)

    result = client.simulate_get(
        "/fragments/query", params={"number": str(fragment.number)}
    )
    guest_result = guest_client.simulate_get(
        "/fragments/query", params={"number": str(fragment.number)}
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([query_item_of(fragment)], 0)
    assert guest_result.status == falcon.HTTP_OK
    assert guest_result.json == query_result_of([], 0)


def test_search_with_scopes_limit_summary(client, guest_client, fragmentarium):
    fragment = FragmentFactory.build(
        authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS]
    )
    fragmentarium.create(fragment)

    result = client.simulate_get(
        "/fragments/query",
        params={"number": str(fragment.number), "limit": "1"},
    )
    guest_result = guest_client.simulate_get(
        "/fragments/query",
        params={"number": str(fragment.number), "limit": "1"},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([query_summary_of(fragment)], 0)
    assert guest_result.status == falcon.HTTP_OK
    assert guest_result.json == query_result_of([], 0)


@pytest.mark.parametrize(
    "params,expected",
    [
        ({"scriptPeriod": Period.NEO_BABYLONIAN.long_name}, [0]),
        ({"scriptPeriod": Period.OLD_ASSYRIAN.long_name}, [1, 2]),
        (
            {
                "scriptPeriod": Period.OLD_ASSYRIAN.long_name,
                "scriptPeriodModifier": PeriodModifier.LATE.value,
            },
            [2],
        ),
        ({"scriptPeriod": Period.NEO_BABYLONIAN.long_name}, [0]),
    ],
)
def test_search_script_period(client, fragmentarium, params, expected):
    fragments = [
        FragmentFactory.build(script=Script(Period.NEO_BABYLONIAN)),
        FragmentFactory.build(script=Script(Period.OLD_ASSYRIAN, PeriodModifier.EARLY)),
        FragmentFactory.build(script=Script(Period.OLD_ASSYRIAN, PeriodModifier.LATE)),
    ]
    for fragment in fragments:
        fragmentarium.create(fragment)

    result = client.simulate_get("/fragments/query", params=params)

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [query_item_of(fragments[index]) for index in expected],
        0,
    )


@pytest.mark.parametrize(
    "project",
    [
        ResearchProject.CAIC,
        ResearchProject.ALU_GENEVA,
        ResearchProject.AMPS,
        ResearchProject.RECC,
    ],
)
def test_search_project(client, fragmentarium, project):
    fragments = [
        FragmentFactory.build(projects=(candidate,)) for candidate in ResearchProject
    ]
    for fragment in fragments:
        fragmentarium.create(fragment)

    result = client.simulate_get(
        "/fragments/query",
        params={"project": project.abbreviation},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [
            query_item_of(fragment)
            for fragment in fragments
            if project in fragment.projects
        ],
        0,
    )


@pytest.mark.parametrize(
    "museum",
    [Museum.THE_BRITISH_MUSEUM, Museum.THE_IRAQ_MUSEUM, Museum.PENN_MUSEUM],
)
def test_search_museum(client, fragmentarium, museum):
    fragments = [
        FragmentFactory.build(museum=candidate)
        for candidate in [museum, Museum.YALE_PEABODY_COLLECTION]
    ]
    for fragment in fragments:
        fragmentarium.create(fragment)

    result = client.simulate_get("/fragments/query", params={"museum": museum.name})

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [
            query_item_of(fragment)
            for fragment in fragments
            if fragment.museum == museum
        ],
        0,
    )


@pytest.mark.parametrize(
    "site",
    [
        get_provenance_record("UR"),
        get_provenance_record("TELL_EL_AMARNA"),
        get_provenance_record("KIS"),
    ],
)
@pytest.mark.parametrize("attribute", ["long_name", "id"])
def test_search_site(client, fragmentarium, site, attribute):
    fragments = [
        FragmentFactory.build(archaeology__site=candidate)
        for candidate in [site, get_provenance_record("ASSUR")]
    ]
    for fragment in fragments:
        fragmentarium.create(fragment)

    result = client.simulate_get(
        "/fragments/query",
        params={"site": getattr(site, attribute)},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of(
        [
            query_item_of(fragment)
            for fragment in fragments
            if fragment.archaeology.site == site
        ],
        0,
    )


@pytest.mark.parametrize(
    "parent_site",
    [
        get_provenance_record("ASSYRIA"),
        get_provenance_record("BABYLONIA"),
        get_provenance_record("PERIPHERY"),
    ],
)
@pytest.mark.parametrize("attribute", ["long_name", "id"])
def test_search_parent_site_returns_no_results(
    client, fragmentarium, parent_site, attribute
):
    fragmentarium.create(
        FragmentFactory.build(archaeology__site=get_provenance_record("UR"))
    )

    result = client.simulate_get(
        "/fragments/query",
        params={"site": getattr(parent_site, attribute)},
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([], 0)


def test_query_latest(client, fragmentarium):
    start_date = date(2023, 5, 1)
    fragments = [
        TransliteratedFragmentFactory.build(
            record=RecordFactory.build(
                entries=(
                    RecordEntryFactory.build(
                        date=str(start_date + timedelta(index)),
                        type=RecordType.TRANSLITERATION,
                    ),
                )
            ),
        )
        for index in range(LATEST_TRANSLITERATION_LIMIT + 10)
    ]
    for fragment in fragments:
        fragmentarium.create(fragment)

    result = client.simulate_get("/fragments/latest")

    assert result.status == falcon.HTTP_OK
    assert result.json == {
        "items": [
            query_item_of(
                fragment,
                list(range(LATEST_TRANSLITERATION_LINE_LIMIT)),
                0,
            )
            for fragment in reversed(fragments[:])
        ][:LATEST_TRANSLITERATION_LIMIT],
        "matchCountTotal": 0,
    }
