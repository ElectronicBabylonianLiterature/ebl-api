from typing import cast
from ebl.fragmentarium.application.fragmentarium import Fragmentarium
import falcon
import pytest
from falcon import testing

from ebl.tests.fragmentarium.findspot_query_test_helpers import (
    assert_findspot_query_visibility,
)
from ebl.common.query.parameter_parser import (
    MAX_FINDSPOT_ID,
    MAX_FINDSPOT_ID_RAW_LENGTH,
    parse_findspot_id,
)
from ebl.errors import DataError
from ebl.fragmentarium.domain.archaeology import Archaeology
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.fragmentarium.fragment_query_test_helpers import (
    query_item_of,
    query_result_of,
)
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_search_findspot_id(
    client: testing.TestClient, fragmentarium: Fragmentarium
) -> None:
    matching = FragmentFactory.build(
        number=MuseumNumber.of("X.1"),
        archaeology=Archaeology(findspot_id=123),
    )
    fragmentarium.create(matching)
    fragmentarium.create(
        FragmentFactory.build(
            number=MuseumNumber.of("X.2"),
            archaeology=Archaeology(findspot_id=456),
        )
    )

    result = cast(
        testing.Result,
        client.simulate_get("/fragments/query", params={"findspotId": "123"}),
    )

    assert result.status == falcon.HTTP_OK
    assert result.json == query_result_of([query_item_of(matching)], 0)


def test_search_findspot_id_preserves_visibility(
    client: testing.TestClient,
    guest_client: testing.TestClient,
    fragmentarium: Fragmentarium,
) -> None:
    assert_findspot_query_visibility(
        client, guest_client, fragmentarium, {"findspotId": "123"}
    )


@pytest.mark.parametrize(
    "value", ["invalid", "-1", "1_0", "true", "1.0", str(MAX_FINDSPOT_ID + 1)]
)
def test_search_findspot_id_rejects_invalid_values(
    client: testing.TestClient, value: str
) -> None:
    result = cast(
        testing.Result,
        client.simulate_get("/fragments/query", params={"findspotId": value}),
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_search_findspot_id_accepts_zero(client: testing.TestClient) -> None:
    result = cast(
        testing.Result,
        client.simulate_get("/fragments/query", params={"findspotId": "0"}),
    )

    assert result.status == falcon.HTTP_OK


def test_parse_findspot_id_accepts_whitespace_and_bson_max() -> None:
    assert parse_findspot_id({"findspotId": f" {MAX_FINDSPOT_ID} "}) == {
        "findspotId": MAX_FINDSPOT_ID
    }


@pytest.mark.parametrize(
    "value", ["0" * 64, "0" * 63 + "1", "0" * 45 + str(MAX_FINDSPOT_ID)]
)
def test_parse_findspot_id_accepts_padded_values(value: str) -> None:
    assert parse_findspot_id({"findspotId": value}) == {"findspotId": int(value)}


def test_parse_findspot_id_rejects_over_raw_length_limit() -> None:
    value = "1" * (MAX_FINDSPOT_ID_RAW_LENGTH + 1)
    with pytest.raises(DataError, match="must not exceed"):
        parse_findspot_id({"findspotId": value})


def test_parse_findspot_id_rejects_oversized_digit_count() -> None:
    with pytest.raises(DataError, match=f"must not exceed {MAX_FINDSPOT_ID}"):
        parse_findspot_id({"findspotId": "1" * 20})


def test_search_findspot_id_rejects_over_raw_length_limit(
    client: testing.TestClient,
) -> None:
    value = "1" * (MAX_FINDSPOT_ID_RAW_LENGTH + 1)
    result = cast(
        testing.Result,
        client.simulate_get("/fragments/query", params={"findspotId": value}),
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("parameter", ["findspotId", "findspotIds"])
def test_search_rejects_repeated_findspot_parameters(
    guest_client: testing.TestClient, parameter: str
) -> None:
    result = cast(
        testing.Result,
        guest_client.simulate_get(f"/fragments/query?{parameter}=1&{parameter}=2"),
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


@pytest.mark.parametrize("value", [" 123 ", "0123"])
def test_findspot_id_normalizes_padding_and_leading_zeros(value: str) -> None:
    assert parse_findspot_id({"findspotId": value})["findspotId"] == 123
