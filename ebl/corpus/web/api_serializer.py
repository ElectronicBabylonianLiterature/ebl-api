from lark.exceptions import ParseError, UnexpectedInput
from marshmallow import ValidationError

from ebl.corpus.domain.text import Text
from ebl.errors import DataError
from ebl.corpus.web.text_schemas import ApiTextSchema


def serialize_public(text: Text):
    return ApiTextSchema(exclude=("chapters",)).dump(text)


def serialize(text: Text) -> dict:
    return ApiTextSchema().dump(text)


def deserialize(data: dict) -> Text:
    try:
        return ApiTextSchema().load(data)
    except (ValueError, ParseError, UnexpectedInput, ValidationError) as error:
        raise DataError(error)
