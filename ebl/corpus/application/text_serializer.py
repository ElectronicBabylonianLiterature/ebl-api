from typing import Optional

from ebl.errors import Defect
from ebl.corpus.application.schemas import ChapterSchema
from ebl.corpus.domain.text import Chapter, Text
from ebl.corpus.domain.text_visitor import TextVisitor


class TextSerializer(TextVisitor):
    @classmethod
    def serialize(cls, text: Text):
        serializer = cls()
        text.accept(serializer)
        return serializer.text

    def __init__(self):
        super().__init__(TextVisitor.Order.PRE)
        self._text: Optional[dict] = None
        self._manuscript: Optional[dict] = None

    @property
    def text(self) -> dict:
        if self._text is None:
            raise Defect("Text accessed before set.")
        else:
            return self._text  # pyre-ignore[7]

    @text.setter
    def text(self, text: dict) -> None:
        self._text = text

    def visit_text(self, text: Text) -> None:
        self.text = {
            "category": text.category,
            "index": text.index,
            "name": text.name,
            "numberOfVerses": text.number_of_verses,
            "approximateVerses": text.approximate_verses,
            "chapters": [],
        }

    def visit_chapter(self, chapter: Chapter) -> None:
        self.text["chapters"].append(ChapterSchema().dump(chapter))  # pyre-ignore[16]


class TextDeserializer:
    @classmethod
    def deserialize(cls, text: dict):
        return cls().deserialize_text(text)

    def deserialize_text(self, text: dict) -> Text:
        return Text(
            text["category"],
            text["index"],
            text["name"],
            text["numberOfVerses"],
            text["approximateVerses"],
            tuple(self.deserialize_chapter(chapter) for chapter in text["chapters"]),
        )

    def deserialize_chapter(self, chapter: dict) -> Chapter:
        return ChapterSchema().load(chapter)  # pyre-ignore[16]


def serialize(text: Text) -> dict:
    return TextSerializer.serialize(text)


def deserialize(dictionary: dict) -> Text:
    return TextDeserializer.deserialize(dictionary)
