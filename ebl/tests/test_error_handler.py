import falcon
from falcon import testing
import pytest

import ebl.error_handler
from ebl.dispatcher import DispatchError
from ebl.errors import DataError, DuplicateError, NotFoundError
from ebl.lemmatization.domain.lemmatization import LemmatizationError
from ebl.transliteration.domain.alignment import AlignmentError


class ErrorResource:
    def __init__(self, exception: Exception):
        self._exception = exception

    def on_get(self, _req: falcon.Request, _resp: falcon.Response) -> None:
        raise self._exception


def simulate_error(exception: Exception) -> str:
    api = falcon.App()
    ebl.error_handler.set_up(api)
    api.add_route("/error", ErrorResource(exception))
    client = testing.TestClient(api)
    return client.simulate_get("/error").status


@pytest.mark.parametrize(
    "exception,expected_status",
    [
        (DataError("invalid"), falcon.HTTP_UNPROCESSABLE_ENTITY),
        (DuplicateError("duplicate"), falcon.HTTP_CONFLICT),
        (NotFoundError("missing"), falcon.HTTP_NOT_FOUND),
        (AlignmentError("invalid"), falcon.HTTP_UNPROCESSABLE_ENTITY),
        (LemmatizationError("invalid"), falcon.HTTP_UNPROCESSABLE_ENTITY),
        (DispatchError("invalid"), falcon.HTTP_UNPROCESSABLE_ENTITY),
    ],
)
def test_error_handler_mapping(exception: Exception, expected_status: str) -> None:
    assert simulate_error(exception) == expected_status
