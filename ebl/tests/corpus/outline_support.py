from typing import Any, Mapping, Sequence, cast
from unittest.mock import create_autospec

from marshmallow import Schema

from ebl.corpus.application.schemas import ChapterSchema
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_outline import ChapterOutline
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.corpus.web.chapter_outline_schemas import ChapterOutlineSchema
from ebl.errors import NotFoundError
from ebl.provenance.application.provenance_repository import ProvenanceRepository
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.provenance.domain.provenance_model import ProvenanceRecord
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
)
from ebl.tests.factories.provenance import build_provenance_records
from ebl.tests.transliteration.storage_test_helpers import stored_dump
from ebl.transliteration.domain.line_number import LineNumber, LineNumberRange
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.normalized_akkadian import AkkadianWord, Caesura
from ebl.transliteration.domain.note_line import NoteLine
from ebl.transliteration.domain.parallel_line import ParallelComposition
from ebl.transliteration.domain.tokens import LanguageShift, Token, ValueToken
from ebl.transliteration.domain.translation_line import Extent, TranslationLine

RECONSTRUCTION: Sequence[Token] = (
    LanguageShift.normalized_akkadian(),
    AkkadianWord.of((ValueToken.of("enūma"),)),
    Caesura.certain(),
    AkkadianWord.of((ValueToken.of("eliš"),)),
)
OUTLINE_CHAPTER_KEYS: Sequence[str] = (
    "textId",
    "classification",
    "stage",
    "version",
    "name",
    "order",
    "uncertainFragments",
)
OUTLINE_MANUSCRIPT_KEYS: Sequence[str] = (
    "id",
    "siglumDisambiguator",
    "museumNumber",
    "accession",
    "periodModifier",
    "period",
    "provenance",
    "type",
    "notes",
    "references",
)
OUTLINE_LINE_KEYS: Sequence[str] = (
    "number",
    "isSecondLineOfParallelism",
    "isBeginningOfSection",
    "translation",
)
OUTLINE_VARIANT_KEYS: Sequence[str] = ("reconstruction", "note", "parallelLines")
API_OUTLINE_VARIANT_KEYS: Sequence[str] = ("reconstruction",)
PROVENANCES_BY_LONG_NAME: Mapping[str, ProvenanceRecord] = {
    record.long_name: record for record in build_provenance_records()
}


def _query_provenance_by_long_name(long_name: str) -> ProvenanceRecord:
    try:
        return PROVENANCES_BY_LONG_NAME[long_name]
    except KeyError as error:
        raise NotFoundError(f"Provenance {long_name} not found.") from error


def create_provenance_service() -> ProvenanceService:
    repository = create_autospec(ProvenanceRepository, instance=True)
    repository.query_by_long_name.side_effect = _query_provenance_by_long_name
    return ProvenanceService(repository)


def dump_to_dict(schema: Schema, value: object) -> dict[str, Any]:
    return cast(dict[str, Any], schema.dump(value))


def _pick(document: Mapping[str, Any], keys: Sequence[str]) -> dict[str, Any]:
    return {key: document[key] for key in keys}


def _create_outline_variant(
    variant: Mapping[str, Any], variant_keys: Sequence[str]
) -> dict[str, Any]:
    return {
        **_pick(variant, variant_keys),
        "manuscriptIds": [
            manuscript_line["manuscriptId"]
            for manuscript_line in variant["manuscripts"]
        ],
    }


def _create_outline_line(
    line: Mapping[str, Any], variant_keys: Sequence[str]
) -> dict[str, Any]:
    return {
        **_pick(line, OUTLINE_LINE_KEYS),
        "variants": [
            _create_outline_variant(variant, variant_keys)
            for variant in line["variants"]
        ],
    }


def project_outline_document(document: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **_pick(document, OUTLINE_CHAPTER_KEYS),
        "manuscripts": [
            _pick(manuscript, OUTLINE_MANUSCRIPT_KEYS)
            for manuscript in document["manuscripts"]
        ],
        "lines": [
            _create_outline_line(line, OUTLINE_VARIANT_KEYS)
            for line in document["lines"]
        ],
    }


def create_outline_document(chapter: Chapter) -> dict[str, Any]:
    return project_outline_document(stored_dump(ChapterSchema(), chapter))


def create_expected_outline_line(
    index: int, api_line: Mapping[str, Any]
) -> dict[str, Any]:
    return {
        "index": index,
        **_create_outline_line(api_line, API_OUTLINE_VARIANT_KEYS),
    }


def dump_outline(chapter: Chapter, revision: str = LEGACY_REVISION) -> dict[str, Any]:
    return dump_to_dict(
        ChapterOutlineSchema(), ChapterOutline.of_chapter(chapter, revision)
    )


def remove_key(document: Mapping[str, Any], removed_key: str) -> dict[str, Any]:
    return {key: value for key, value in document.items() if key != removed_key}


def remove_token_fields(line: Mapping[str, Any]) -> dict[str, Any]:
    return {
        **line,
        "variants": [
            {
                **remove_key(variant, "reconstructionTokens"),
                "manuscripts": [
                    remove_key(manuscript_line, "atfTokens")
                    for manuscript_line in variant["manuscripts"]
                ],
            }
            for variant in line["variants"]
        ],
    }


def create_chapter_with_lines(line_count: int) -> Chapter:
    return ChapterFactory.build(
        lines=tuple(LineFactory.build_batch(line_count, manuscript_id=1))
    )


def create_outline_chapter() -> Chapter:
    first_manuscript = ManuscriptFactory.build(
        id=1,
        siglum_disambiguator="1a",
        museum_number=MuseumNumber.of("K.5419.C"),
        accession="",
        with_old_sigla=True,
    )
    second_manuscript = ManuscriptFactory.build(
        id=5, siglum_disambiguator="2", museum_number=None, accession="A.12"
    )
    first_line = LineFactory.build(
        number=LineNumber(1),
        translation=(
            TranslationLine((StringPart("When on high"),), "en", Extent(LineNumber(2))),
            TranslationLine((StringPart("bar"),), "ar", None),
        ),
        variants=(
            LineVariantFactory.build(
                note=NoteLine((StringPart("a note"),)),
                parallel_lines=(ParallelComposition(False, "name", LineNumber(7)),),
                manuscripts=(
                    ManuscriptLineFactory.build(manuscript_id=first_manuscript.id),
                    ManuscriptLineFactory.build(manuscript_id=second_manuscript.id),
                ),
            ),
            LineVariantFactory.build(note=None, parallel_lines=(), manuscripts=()),
        ),
    )
    second_line = LineFactory.build(
        number=LineNumber(2),
        translation=(),
        variants=(
            LineVariantFactory.build(
                note=None,
                manuscripts=(
                    ManuscriptLineFactory.build(manuscript_id=second_manuscript.id),
                ),
            ),
        ),
    )
    third_line = LineFactory.build(
        number=LineNumberRange(LineNumber(3), LineNumber(4, True)),
        variants=(
            LineVariantFactory.build(
                manuscripts=(
                    ManuscriptLineFactory.build(manuscript_id=first_manuscript.id),
                ),
            ),
        ),
    )
    return ChapterFactory.build(
        manuscripts=(first_manuscript, second_manuscript),
        uncertain_fragments=(MuseumNumber.of("K.1"), MuseumNumber.of("BM.2.a")),
        lines=(first_line, second_line, third_line),
    )
