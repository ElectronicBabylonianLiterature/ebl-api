import falcon
from falcon import testing
import pytest

import ebl.error_handler
from ebl.dispatcher import DispatchError
from ebl.errors import ConflictError, DataError, DuplicateError, NotFoundError
from ebl.lemmatization.domain.lemmatization import LemmatizationError
from ebl.transliteration.domain.alignment import AlignmentError


class ErrorResource:
    def __init__(self, exception: Exception):
        self._exception = exception

    def on_get(self, _req: falcon.Request, _resp: falcon.Response) -> None:
        raise self._exception


def get_error_result(exception: Exception) -> testing.Result:
    api = falcon.App()
    ebl.error_handler.set_up(api)
    api.add_route("/error", ErrorResource(exception))
    client = testing.TestClient(api)
    result = client.simulate_get("/error")
    assert isinstance(result, testing.Result)
    return result


def simulate_error(exception: Exception) -> str:
    return get_error_result(exception).status


@pytest.mark.parametrize(
    "exception,expected_status",
    [
        (DataError("invalid"), falcon.HTTP_UNPROCESSABLE_ENTITY),
        (DuplicateError("duplicate"), falcon.HTTP_CONFLICT),
        (ConflictError("conflict"), falcon.HTTP_CONFLICT),
        (NotFoundError("missing"), falcon.HTTP_NOT_FOUND),
        (AlignmentError("invalid"), falcon.HTTP_UNPROCESSABLE_ENTITY),
        (LemmatizationError("invalid"), falcon.HTTP_UNPROCESSABLE_ENTITY),
        (DispatchError("invalid"), falcon.HTTP_UNPROCESSABLE_ENTITY),
        (RuntimeError("unexpected"), falcon.HTTP_INTERNAL_SERVER_ERROR),
        (falcon.HTTPForbidden(), falcon.HTTP_FORBIDDEN),
    ],
)
def test_error_handler_mapping(exception: Exception, expected_status: str) -> None:
    assert simulate_error(exception) == expected_status


def test_conflict_error_is_described_in_the_response() -> None:
    result = get_error_result(ConflictError("the chapter has changed"))

    assert result.status == falcon.HTTP_CONFLICT
    assert result.json == {
        "title": "409 Conflict",
        "description": "the chapter has changed",
    }
