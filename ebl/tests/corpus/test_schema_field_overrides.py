import inspect
from pathlib import Path
from typing import Any, cast

from ebl.common.domain.stage import Stage
from marshmallow import fields

from ebl.corpus.application import line_schemas, manuscript_schemas, schemas
from ebl.corpus.application.id_schemas import TextIdSchema
from ebl.corpus.domain.dictionary_display import DictionaryLineDisplay
from ebl.corpus.domain.dictionary_line import DictionaryLine
from ebl.corpus.web.chapter_info_schema import ChapterInfoLineSchema
from ebl.corpus.web.chapter_schemas import ApiLineSchema
from ebl.corpus.web.display_schemas import DictionaryLineDisplaySchema
from ebl.corpus.domain.line import Line
from ebl.corpus.domain.line_variant import LineVariant
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.text_id import TextId
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.application.line_schemas import TranslationLineSchema
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.translation_line import TranslationLine


def test_public_schema_imports_reexport_the_original_classes() -> None:
    assert schemas.ManuscriptSchema is manuscript_schemas.ManuscriptSchema
    assert schemas.OldSiglumSchema is manuscript_schemas.OldSiglumSchema
    assert schemas.LineSchema is line_schemas.LineSchema
    assert schemas.LineVariantSchema is line_schemas.LineVariantSchema
    assert schemas.DictionaryLineSchema is line_schemas.DictionaryLineSchema
    assert schemas.ManuscriptLineSchema is line_schemas.ManuscriptLineSchema
    assert (
        schemas.DictionaryLinePaginationSchema
        is line_schemas.DictionaryLinePaginationSchema
    )
    for name in (
        "OldSiglumSchema",
        "ManuscriptSchema",
        "ManuscriptLineSchema",
        "LineVariantSchema",
        "LineSchema",
        "DictionaryLineSchema",
        "DictionaryLinePaginationSchema",
    ):
        schema = getattr(schemas, name)
        module = (
            manuscript_schemas
            if name in {"OldSiglumSchema", "ManuscriptSchema"}
            else line_schemas
        )
        assert inspect.getmodule(schema) is module
        assert module.__file__ is not None
        assert Path(inspect.getfile(schema)) == Path(module.__file__)
        assert f"class {name}(Schema):" in inspect.getsource(schema)


def test_chapter_info_translation_override_retains_structured_payload() -> None:
    translation = TranslationLine((StringPart("Meaning"),), "en", None)
    line = Line(LineNumber(1), (LineVariant(()),), translation=(translation,))

    assert isinstance(ApiLineSchema().fields["translation"], fields.Function)
    assert isinstance(ChapterInfoLineSchema().fields["translation"], fields.List)
    assert (
        cast(dict[str, Any], ApiLineSchema().dump(line))["translation"]
        == translation.atf
    )
    assert cast(dict[str, Any], ChapterInfoLineSchema().dump(line))["translation"] == [
        TranslationLineSchema().dump(translation)
    ]


def test_dictionary_display_omits_manuscripts_and_retains_line_details() -> None:
    text_id = TextId(Genre.LITERATURE, 1, 1)
    dictionary_line = DictionaryLine(
        text_id,
        "Example text",
        "Chapter",
        Stage.OLD_BABYLONIAN,
        Line(LineNumber(1), (LineVariant(()),)),
    )
    display = DictionaryLineDisplay.from_dictionary_line(dictionary_line)

    payload = cast(dict[str, Any], DictionaryLineDisplaySchema().dump(display))

    assert "manuscripts" not in payload
    assert payload["textId"] == TextIdSchema().dump(text_id)
    assert payload["lineDetails"]["variants"]
    assert payload["line"] == schemas.LineSchema().dump(dictionary_line.line)
