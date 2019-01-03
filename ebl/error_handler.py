import logging
import falcon
from ebl.dispatcher import DispatchError
from ebl.errors import NotFoundError
from ebl.text.lemmatization import LemmatizationError


def http_error(ex, _req, _resp, _params):
    raise ex


def unexpected_error(_ex, _req, _resp, _params):
    logging.exception('Unexpected Exception')
    raise falcon.HTTPInternalServerError()


def unprocessable_entity(ex, _req, _resp, _params):
    raise falcon.HTTPUnprocessableEntity(description=str(ex))


def not_found_error(ex, _req, _resp, _params):
    raise falcon.HTTPNotFound(description=str(ex))


def set_up(api):
    api.add_error_handler(Exception, unexpected_error)
    api.add_error_handler(DispatchError, unprocessable_entity)
    api.add_error_handler(LemmatizationError, unprocessable_entity)
    api.add_error_handler(NotFoundError, not_found_error)
    api.add_error_handler(falcon.HTTPError, http_error)
    api.add_error_handler(falcon.HTTPStatus, http_error)
