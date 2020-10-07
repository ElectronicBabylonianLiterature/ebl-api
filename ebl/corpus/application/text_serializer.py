from typing import Optional, Type

from ebl.errors import Defect
from ebl.corpus.application.schemas import ManuscriptSchema
from ebl.transliteration.domain.reconstructed_text_parser import (
    parse_reconstructed_line,
)
from ebl.corpus.domain.enums import Classification, Stage
from ebl.corpus.domain.text import Chapter, Line, Manuscript, ManuscriptLine, Text
from ebl.corpus.domain.text_visitor import TextVisitor
from ebl.transliteration.application.line_schemas import TextLineSchema
from ebl.transliteration.domain.labels import parse_label
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.domain.atf_visitor import convert_to_atf


class TextSerializer(TextVisitor):
    @classmethod
    def serialize(cls, text: Text):
        serializer = cls()
        text.accept(serializer)
        return serializer.text

    def __init__(
        self, manuscript_schema_type: Type[ManuscriptSchema] = ManuscriptSchema
    ) -> None:
        super().__init__(TextVisitor.Order.PRE)
        self._manuscript_schema = manuscript_schema_type()
        self._text: Optional[dict] = None
        self._chapter: Optional[dict] = None
        self._manuscript: Optional[dict] = None
        self._line: Optional[dict] = None
        self._manuscript_line: Optional[dict] = None

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

    @property
    def line(self) -> dict:
        if self._line is None:
            raise Defect("Line accessed before set.")
        else:
            return self._line  # pyre-ignore[7]

    @line.setter
    def line(self, line: dict) -> None:
        self._line = line

    @property
    def manuscript(self) -> dict:
        if self._manuscript is None:
            raise Defect("Manuscript accessed before set.")
        else:
            return self._manuscript  # pyre-ignore[7]

    @manuscript.setter
    def manuscript(self, manuscript: dict) -> None:
        self._manuscript = manuscript

    @property
    def manuscript_line(self) -> dict:
        if self._manuscript_line is None:
            raise Defect("Manuscript line accessed before set.")
        else:
            return self._manuscript_line  # pyre-ignore[7]

    @manuscript_line.setter
    def manuscirpt_line(self, manuscript_line: dict) -> None:
        self._manuscript_line = manuscript_line

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
        self.manuscript = self._manuscript_schema.dump(manuscript)
        self.chapter["manuscripts"].append(self.manuscript)

    def visit_line(self, line: Line) -> None:
        self.line = {
            "number": OneOfLineNumberSchema().dump(line.number),  # pyre-ignore[16]
            "reconstruction": convert_to_atf(None, line.reconstruction),
            "manuscripts": [],
        }
        self.chapter["lines"].append(self.line)

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        self.line["manuscripts"].append(
            {
                "manuscriptId": manuscript_line.manuscript_id,
                "labels": [label.to_value() for label in manuscript_line.labels],
                "line": TextLineSchema().dump(manuscript_line.line),  # pyre-ignore[16]
            }
        )


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
        return Line(
            OneOfLineNumberSchema().load(line["number"]),  # pyre-ignore[16]
            parse_reconstructed_line(line["reconstruction"]),
            False,
            False,
            tuple(
                self.deserialize_manuscript_line(line) for line in line["manuscripts"]
            ),
        )

    def deserialize_manuscript_line(self, manuscript_line: dict) -> ManuscriptLine:
        return ManuscriptLine(
            manuscript_line["manuscriptId"],
            tuple(parse_label(label) for label in manuscript_line["labels"]),
            TextLineSchema().load(manuscript_line["line"]),  # pyre-ignore[16]
        )


def serialize(text: Text) -> dict:
    return TextSerializer.serialize(text)


def deserialize(dictionary: dict) -> Text:
    return TextDeserializer.deserialize(dictionary)
