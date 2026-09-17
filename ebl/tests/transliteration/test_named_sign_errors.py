from typing import Any, Dict, cast

import falcon
import pytest
from falcon import testing
from marshmallow import ValidationError

import ebl.error_handler
from ebl.errors import DataError
from ebl.transliteration.application.token_schemas_signs import (
    NamedSignSchema,
    ReadingSchema,
)
from ebl.transliteration.domain.enclosure_tokens import BrokenAway
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.signs_transformer import name_arguments
from ebl.transliteration.domain.tokens import ValueToken

K = ValueToken.of("k")
U = ValueToken.of("u")
CLOSE = BrokenAway.close()
BROKEN_NAME = (K, CLOSE, U)


def _dumped_reading() -> Dict[str, Any]:
    reading = Reading.of_arguments(name_arguments(BROKEN_NAME))
    return cast(Dict[str, Any], ReadingSchema().dump(reading))


def _status_for(payload: Dict[str, Any]) -> str:
    class LoadingResource:
        def on_get(self, _req: falcon.Request, _resp: falcon.Response) -> None:
            ReadingSchema().load(payload)

    api = falcon.App()
    ebl.error_handler.set_up(api)
    api.add_route("/reading", LoadingResource())
    return testing.TestClient(api).simulate_get("/reading").status


def test_more_breaks_than_parts_is_a_data_error_not_a_value_error() -> None:
    payload = _dumped_reading()
    payload["nameBreaks"] = payload["nameBreaks"] * 3

    with pytest.raises(DataError, match="at most 2 breaks, not 3"):
        ReadingSchema().load(payload)


def test_more_breaks_than_parts_is_unprocessable_on_a_route() -> None:
    payload = _dumped_reading()
    payload["nameBreaks"] = payload["nameBreaks"] * 3

    status = _status_for(payload)

    assert status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_a_negative_sub_index_is_unprocessable_on_a_route() -> None:
    payload = _dumped_reading()
    payload["subIndex"] = -1

    status = _status_for(payload)

    assert status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_absent_name_breaks_is_read_as_the_legacy_interleaved_format() -> None:
    dumped = _dumped_reading()
    legacy = {key: value for key, value in dumped.items() if key != "nameBreaks"}
    legacy["nameParts"] = [
        dumped["nameParts"][0],
        dumped["nameBreaks"][0],
        dumped["nameParts"][1],
    ]

    loaded = cast(Reading, ReadingSchema().load(legacy))

    assert loaded.name_parts == (K, U)
    assert loaded.name_breaks == (CLOSE,)


def test_name_breaks_is_required_when_name_parts_cannot_be_separated() -> None:
    payload = _dumped_reading()
    del payload["nameBreaks"]
    payload["nameParts"] = "ku"

    with pytest.raises(ValidationError) as error:
        NamedSignSchema().load(payload)

    assert "nameBreaks" in error.value.messages
