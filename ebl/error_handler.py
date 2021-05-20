import logging

import falcon

from ebl.dispatcher import DispatchError
from ebl.errors import DataError, DuplicateError, NotFoundError
from ebl.lemmatization.domain.lemmatization import LemmatizationError
from ebl.transliteration.domain.alignment import AlignmentError


def http_error(_req, _resp, ex, _params):
    raise ex


def unexpected_error(_req, _resp, _ex, _params):
    logging.exception("Unexpected Exception")
    raise falcon.HTTPInternalServerError()


def unprocessable_entity(_req, _resp, ex, _params):
    raise falcon.HTTPUnprocessableEntity(description=str(ex))


def not_found_error(_req, _resp, ex, _params):
    raise falcon.HTTPNotFound(description=str(ex))


def duplicate_error(_req, _resp, ex, _params):
    raise falcon.HTTPConflict(description=str(ex))


def set_up(api):
    api.add_error_handler(Exception, unexpected_error)
    api.add_error_handler(AlignmentError, unprocessable_entity)
    api.add_error_handler(DispatchError, unprocessable_entity)
    api.add_error_handler(LemmatizationError, unprocessable_entity)
    api.add_error_handler(NotFoundError, not_found_error)
    api.add_error_handler(DuplicateError, duplicate_error)
    api.add_error_handler(DataError, unprocessable_entity)
    api.add_error_handler(falcon.HTTPError, http_error)
    api.add_error_handler(falcon.HTTPStatus, http_error)
