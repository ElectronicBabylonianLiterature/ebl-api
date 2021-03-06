from lark.exceptions import ParseError, UnexpectedInput  # pyre-ignore[21]
from marshmallow import ValidationError  # pyre-ignore[21]

from ebl.corpus.domain.text import Text
from ebl.errors import DataError
from ebl.corpus.web.text_schemas import ApiTextSchema


def serialize_public(text: Text):
    return ApiTextSchema(exclude=("chapters",)).dump(text)  # pyre-ignore[16,28]


def serialize(text: Text) -> dict:
    return ApiTextSchema().dump(text)  # pyre-ignore[16]


def deserialize(data: dict) -> Text:
    try:
        return ApiTextSchema().load(data)  # pyre-ignore[16]
    except (ValueError, ParseError, UnexpectedInput, ValidationError) as error:
        raise DataError(error)
