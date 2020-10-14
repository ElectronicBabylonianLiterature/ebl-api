from typing import Sequence

from lark.exceptions import ParseError, UnexpectedInput  # pyre-ignore[21]
from marshmallow import ValidationError  # pyre-ignore[21]

from ebl.corpus.application.text_serializer import TextDeserializer, TextSerializer
from ebl.corpus.domain.text import Line, Chapter, Text
from ebl.errors import DataError
from ebl.corpus.application.schemas import ApiChapterSchema, ApiLineSchema


class ApiSerializer(TextSerializer):
    def __init__(self):
        super().__init__()

    @staticmethod
    def serialize_public(text: Text):
        serializer = ApiSerializer()
        serializer.visit_text(text)
        return serializer.text

    def visit_chapter(self, chapter: Chapter) -> None:
        self.text["chapters"].append(
            ApiChapterSchema().dump(chapter)  # pyre-ignore[16]
        )


class ApiDeserializer(TextDeserializer):
    def deserialize_chapter(self, chapter: dict) -> Chapter:
        return ApiChapterSchema().load(chapter)  # pyre-ignore[16]


def serialize(text: Text) -> dict:
    return ApiSerializer.serialize(text)


def deserialize(dto: dict) -> Text:
    try:
        return ApiDeserializer.deserialize(dto)
    except (ValueError, ParseError, UnexpectedInput, ValidationError) as error:
        raise DataError(error)


def deserialize_lines(lines: list) -> Sequence[Line]:
    try:
        return tuple(ApiLineSchema().load(lines, many=True))  # pyre-ignore[16]
    except (ValueError, ParseError, UnexpectedInput, ValidationError) as error:
        raise DataError(error)
