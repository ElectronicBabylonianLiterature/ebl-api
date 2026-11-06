from typing import cast

from falcon import testing

from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import (
    query_item_of,
    query_result_of,
)


def assert_findspot_query_visibility(
    client: testing.TestClient,
    guest_client: testing.TestClient,
    fragmentarium: Fragmentarium,
    parameters: dict[str, str],
) -> None:
    fragment = FragmentFactory.build(
        archaeology=Archaeology(findspot_id=123),
        authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS],
    )
    fragmentarium.create(fragment)
    authorized_result = cast(
        testing.Result, client.simulate_get("/fragments/query", params=parameters)
    )
    guest_result = cast(
        testing.Result, guest_client.simulate_get("/fragments/query", params=parameters)
    )

    assert authorized_result.json == query_result_of([query_item_of(fragment)], 0)
    assert guest_result.json == query_result_of([], 0)
