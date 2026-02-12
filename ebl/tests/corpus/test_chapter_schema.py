import attr
from ebl.bibliography.application.reference_schema import (
    ApiReferenceSchema,
    ReferenceSchema,
)
from ebl.bibliography.domain.reference import Reference
from ebl.corpus.application.schemas import ChapterSchema, OldSiglumSchema
from ebl.corpus.application.record_schemas import (
    AuthorSchema,
    RecordSchema,
    TranslatorSchema,
)
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.record import Author, AuthorRole, Translator
from ebl.corpus.web.chapter_schemas import ApiOldSiglumSchema
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
)
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.line_schemas import (
    NoteLineSchema,
    TranslationLineSchema,
)
from ebl.transliteration.application.note_line_part_schemas import (
    OneOfNoteLinePartSchema,
)
from ebl.transliteration.application.one_of_line_schema import (
    OneOfLineSchema,
    ParallelLineSchema,
)
from ebl.transliteration.application.text_schema import TextSchema
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.parallel_line import ParallelComposition
from ebl.transliteration.domain.translation_line import TranslationLine

REFERENCES = (ReferenceFactory.build(with_document=True),)
MANUSCRIPT = ManuscriptFactory.build(references=REFERENCES, with_old_sigla=True)
UNCERTAIN_FRAGMENTS = (MuseumNumber.of("K.1"),)
FIRST_MANUSCRIPT_LINE = ManuscriptLineFactory.build(manuscript_id=MANUSCRIPT.id)
SECOND_MANUSCRIPT_LINE = ManuscriptLineFactory.build(manuscript_id=MANUSCRIPT.id)

LINE_VARIANT = LineVariantFactory.build(
    manuscripts=(FIRST_MANUSCRIPT_LINE, SECOND_MANUSCRIPT_LINE),
    parallel_lines=(ParallelComposition(False, "name", LineNumber(2)),),
    intertext=(StringPart("bar"),),
)
TRANSLATION_LINE = TranslationLine((StringPart("foo"),), "en", None)
LINE = LineFactory.build(variants=(LINE_VARIANT,), translation=(TRANSLATION_LINE,))
CHAPTER = ChapterFactory.build(
    manuscripts=(MANUSCRIPT,), uncertain_fragments=UNCERTAIN_FRAGMENTS, lines=(LINE,)
)


def strip_document(reference: Reference) -> Reference:
    return attr.evolve(reference, document=None)


def strip_documents(chapter: Chapter) -> Chapter:
    return attr.evolve(
        chapter,
        manuscripts=tuple(
            attr.evolve(
                manuscript,
                references=tuple(map(strip_document, MANUSCRIPT.references)),
                old_sigla=tuple(
                    attr.evolve(
                        old_siglum,
                        reference=strip_document(old_siglum.reference),
                    )
                    for old_siglum in manuscript.old_sigla
                ),
            )
            for manuscript in chapter.manuscripts
        ),
    )


def get_museum_number(manuscript: Manuscript, include_documents: bool):
    if include_documents:
        return str(manuscript.museum_number) if manuscript.museum_number else ""

    return manuscript.museum_number and MuseumNumberSchema().dump(
        manuscript.museum_number
    )


def to_dict(chapter: Chapter, include_documents=False):
    OLD_SIGLUM_SCHEMA = ApiOldSiglumSchema if include_documents else OldSiglumSchema
    REFERENCE_SCHEMA = ApiReferenceSchema if include_documents else ReferenceSchema

    return {
        "textId": {
            "genre": chapter.text_id.genre.value,
            "category": chapter.text_id.category,
            "index": chapter.text_id.index,
        },
        "classification": chapter.classification.value,
        "stage": chapter.stage.long_name,
        "version": chapter.version,
        "name": chapter.name,
        "order": chapter.order,
        "signs": list(chapter.signs),
        "record": RecordSchema().dump(chapter.record),
        "parserVersion": chapter.parser_version,
        "manuscripts": [
            {
                "id": manuscript.id,
                "siglumDisambiguator": manuscript.siglum_disambiguator,
                "oldSigla": OLD_SIGLUM_SCHEMA().dump(manuscript.old_sigla, many=True),
                "museumNumber": get_museum_number(manuscript, include_documents),
                "accession": manuscript.accession,
                "periodModifier": manuscript.period_modifier.value,
                "period": manuscript.period.long_name,
                "provenance": manuscript.provenance.long_name,
                "type": manuscript.type.long_name,
                "notes": manuscript.notes,
                "colophon": TextSchema().dump(manuscript.colophon),
                "unplacedLines": TextSchema().dump(manuscript.unplaced_lines),
                "references": REFERENCE_SCHEMA().dump(manuscript.references, many=True),
            }
            for manuscript in chapter.manuscripts
        ],
        "uncertainFragments": MuseumNumberSchema().dump(UNCERTAIN_FRAGMENTS, many=True),
        "lines": [
            {
                "number": OneOfLineNumberSchema().dump(line.number),
                "variants": [
                    {
                        "reconstruction": OneOfTokenSchema().dump(
                            variant.reconstruction, many=True
                        ),
                        "note": variant.note and NoteLineSchema().dump(variant.note),
                        "parallelLines": ParallelLineSchema().dump(
                            variant.parallel_lines, many=True
                        ),
                        "intertext": OneOfNoteLinePartSchema().dump(
                            variant.intertext, many=True
                        ),
                        "manuscripts": [
                            {
                                "manuscriptId": manuscript_line.manuscript_id,
                                "labels": [
                                    label.to_value() for label in manuscript_line.labels
                                ],
                                "line": OneOfLineSchema().dump(manuscript_line.line),
                                "paratext": OneOfLineSchema().dump(
                                    manuscript_line.paratext, many=True
                                ),
                                "omittedWords": list(manuscript_line.omitted_words),
                            }
                            for manuscript_line in variant.manuscripts
                        ],
                    }
                    for variant in line.variants
                ],
                "oldLineNumbers": [],
                "isSecondLineOfParallelism": line.is_second_line_of_parallelism,
                "isBeginningOfSection": line.is_beginning_of_section,
                "translation": TranslationLineSchema().dump(
                    line.translation, many=True
                ),
            }
            for line in chapter.lines
        ],
        "isFilteredQuery": False,
        "colophonLinesInQuery": {"colophonLinesInQuery": {}},
    }


def test_dump() -> None:
    assert ChapterSchema().dump(CHAPTER) == to_dict(CHAPTER)


def test_load(seeded_provenance_service) -> None:
    schema = ChapterSchema(
        context={"provenance_service": seeded_provenance_service}
    )
    assert schema.load(to_dict(CHAPTER)) == strip_documents(CHAPTER)


def test_author_schema() -> None:
    author = Author("name", "prefix", AuthorRole.EDITOR, "0000-0000-0000-0000")
    serialized = {
        "name": author.name,
        "prefix": author.prefix,
        "role": author.role.name,
        "orcidNumber": author.orcid_number,
    }

    assert AuthorSchema().dump(author) == serialized
    assert AuthorSchema().load(serialized) == author


def test_translator_schema() -> None:
    translator = Translator("name", "prefix", "0000-0000-0000-0000", "en")
    serialized = {
        "name": translator.name,
        "prefix": translator.prefix,
        "orcidNumber": translator.orcid_number,
        "language": translator.language,
    }

    assert TranslatorSchema().dump(translator) == serialized
    assert TranslatorSchema().load(serialized) == translator
