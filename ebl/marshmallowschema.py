from functools import wraps
from typing import Optional

import falcon  # pyre-ignore[21]
from marshmallow import Schema  # pyre-ignore[21]


def validate(
    req_schema: Optional[Schema] = None,  # pyre-ignore[11]
    resp_schema: Optional[Schema] = None,
):
    def decorator(func):
        @wraps(func)
        def wrapper(self, req, resp, *args, **kwargs):
            if req_schema is not None:
                errors = req_schema.validate(req.media)
                if errors:
                    raise falcon.HTTPBadRequest(
                        "Request data failed validation", description=errors
                    )

            result = func(self, req, resp, *args, **kwargs)

            if resp_schema is not None and resp_schema.validate(resp.media):
                raise falcon.HTTPInternalServerError(
                    "Response data failed validation"
                )

            return result

        return wrapper

    return decorator
