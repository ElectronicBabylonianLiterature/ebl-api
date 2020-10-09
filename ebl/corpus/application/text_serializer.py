from typing import Optional

from ebl.errors import Defect
from ebl.corpus.application.schemas import LineSchema, ManuscriptSchema
from ebl.corpus.domain.enums import Classification, Stage
from ebl.corpus.domain.text import Chapter, Line, Manuscript, Text
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
        self._chapter: Optional[dict] = None
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

    @property
    def chapter(self) -> dict:
        if self._chapter is None:
            raise Defect("Chapter accessed before set.")
        else:
            return self._chapter  # pyre-ignore[7]

    @chapter.setter
    def chapter(self, chapter: dict) -> None:
        self._chapter = chapter

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
        self.chapter = {
            "classification": chapter.classification.value,
            "stage": chapter.stage.value,
            "version": chapter.version,
            "name": chapter.name,
            "order": chapter.order,
            "manuscripts": [],
            "lines": [],
            "parserVersion": chapter.parser_version,
        }
        self.text["chapters"].append(self.chapter)

    def visit_manuscript(self, manuscript: Manuscript) -> None:
        # pyre-ignore[16]
        self.chapter["manuscripts"].append(ManuscriptSchema().dump(manuscript))

    def visit_line(self, line: Line) -> None:
        self.chapter["lines"].append(LineSchema().dump(line))  # pyre-ignore[16]


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
        return Chapter(
            Classification(chapter["classification"]),
            Stage(chapter["stage"]),
            chapter["version"],
            chapter["name"],
            chapter["order"],
            tuple(
                self.deserialize_manuscript(manuscript)
                for manuscript in chapter["manuscripts"]
            ),
            tuple(self.deserialize_line(line) for line in chapter.get("lines", [])),
            chapter.get("parserVersion", ""),
        )

    def deserialize_manuscript(self, manuscript: dict) -> Manuscript:
        return ManuscriptSchema().load(manuscript)  # pyre-ignore[16]

    def deserialize_line(self, line: dict) -> Line:
        return LineSchema().load(line)  # pyre-ignore[16]


def serialize(text: Text) -> dict:
    return TextSerializer.serialize(text)


def deserialize(dictionary: dict) -> Text:
    return TextDeserializer.deserialize(dictionary)
