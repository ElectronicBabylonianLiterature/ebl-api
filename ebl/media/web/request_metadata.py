"""Bound and decode JSON metadata before a media mutation reaches persistence."""

import json

import falcon

from ebl.errors import DataError


def bounded_json_body(req: falcon.Request) -> dict:
    if req.content_length is not None and req.content_length > 16384:
        raise falcon.HTTPPayloadTooLarge(description="Media metadata exceeds 16 KiB.")
    content = req.bounded_stream.read(16385)
    if len(content) > 16384:
        raise falcon.HTTPPayloadTooLarge(description="Media metadata exceeds 16 KiB.")
    try:
        data = json.loads(content) if content else {}
    # 16 KiB of "[" exceeds the decoder's recursion limit: still invalid input.
    except (ValueError, UnicodeDecodeError, RecursionError) as error:
        raise DataError("Invalid JSON metadata.") from error
    if not isinstance(data, dict):
        raise DataError("Media metadata must be an object.")
    return data
