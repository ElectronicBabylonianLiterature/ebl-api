import attr
import falcon
from falcon import testing
import pytest

import ebl.error_handler
from ebl.dispatcher import DispatchError
from ebl.errors import DataError, Defect, DuplicateError, NotFoundError
from ebl.lemmatization.domain.lemmatization import LemmatizationError
from ebl.transliteration.domain.alignment import AlignmentError


class ErrorResource:
    def __init__(self, exception: Exception):
        self._exception = exception

    def on_get(self, _req: falcon.Request, _resp: falcon.Response) -> None:
        raise self._exception


@attr.attrs(auto_attribs=True, frozen=True)
class ErrorResponse:
    status: str
    text: str


def simulate_error(exception: Exception) -> ErrorResponse:
    api = falcon.App()
    ebl.error_handler.set_up(api)
    api.add_route("/error", ErrorResource(exception))
    result = testing.TestClient(api).simulate_get("/error")
    assert isinstance(result, testing.Result)
    return ErrorResponse(status=result.status, text=result.text)


@pytest.mark.parametrize(
    "exception,expected_status",
    [
        (DataError("invalid"), falcon.HTTP_UNPROCESSABLE_ENTITY),
        (DuplicateError("duplicate"), falcon.HTTP_CONFLICT),
        (NotFoundError("missing"), falcon.HTTP_NOT_FOUND),
        (AlignmentError("invalid"), falcon.HTTP_UNPROCESSABLE_ENTITY),
        (LemmatizationError("invalid"), falcon.HTTP_UNPROCESSABLE_ENTITY),
        (DispatchError("invalid"), falcon.HTTP_UNPROCESSABLE_ENTITY),
        (
            Defect("storage handle gridfs-secret-name is missing"),
            falcon.HTTP_INTERNAL_SERVER_ERROR,
        ),
    ],
)
def test_error_handler_mapping(exception: Exception, expected_status: str) -> None:
    assert simulate_error(exception).status == expected_status


def test_defect_response_does_not_leak_internal_details() -> None:
    result = simulate_error(Defect("storage handle gridfs-secret-name is missing"))

    assert result.status == falcon.HTTP_INTERNAL_SERVER_ERROR
    assert "gridfs-secret-name" not in result.text


def test_an_unregistered_exception_becomes_an_internal_server_error() -> None:
    result = simulate_error(RuntimeError("boom"))

    assert result.status == falcon.HTTP_INTERNAL_SERVER_ERROR
    assert "boom" not in result.text


def test_falcon_errors_are_passed_through_unchanged() -> None:
    result = simulate_error(falcon.HTTPBadRequest(description="bad request"))

    assert result.status == falcon.HTTP_BAD_REQUEST
