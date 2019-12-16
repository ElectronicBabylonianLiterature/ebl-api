from functools import wraps
from typing import Optional, Type

import falcon
from marshmallow import Schema


def validate(
    req_schema: Optional[Type[Schema]] = None,
    resp_schema: Optional[Type[Schema]] = None,
):
    def decorator(func):
        @wraps(func)
        def wrapper(self, req, resp, *args, **kwargs):
            if req_schema is not None:
                errors = req_schema().validate(req.media)
                if errors:
                    raise falcon.HTTPBadRequest(
                        "Request data failed validation", description=errors
                    )

            result = func(self, req, resp, *args, **kwargs)

            if resp_schema is not None:
                if resp_schema().validate(resp.media):
                    raise falcon.HTTPInternalServerError(
                        "Response data failed validation"
                    )

            return result

        return wrapper

    return decorator
