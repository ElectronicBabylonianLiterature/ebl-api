from datetime import date, timedelta
from typing import cast

import falcon
from falcon import testing

from ebl.fragmentarium.application.fragmentarium import Fragmentarium

from ebl.fragmentarium.domain.record import RecordType
from ebl.fragmentarium.infrastructure.queries import (
    LATEST_TRANSLITERATION_LIMIT,
    LATEST_TRANSLITERATION_LINE_LIMIT,
)
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.factories.record import RecordEntryFactory, RecordFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import query_item_of


def test_query_latest(client: testing.TestClient, fragmentarium: Fragmentarium) -> None:
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

    result = cast(testing.Result, client.simulate_get("/fragments/latest"))

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
