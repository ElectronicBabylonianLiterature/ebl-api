from typing import Tuple, cast

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.corpus.application.record_schemas import RecordSchema
from ebl.corpus.web.chapter_schemas import (
    ApiChapterSchema,
    ApiManuscriptSchema,
    ApiOldSiglumSchema,
)
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.manuscript_line import ManuscriptLine
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import (
    ChapterFactory,
    ChapterQueryColophonLinesFactory,
    ManuscriptFactory,
)
from ebl.tests.factories.corpus_lines import (
    LineFactory,
    LineVariantFactory,
    ManuscriptLineFactory,
)
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.application.line_number_schemas import OldLineNumberSchema
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.atf_visitor import convert_to_atf
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.parallel_line import ParallelComposition
from ebl.transliteration.domain.text_line import TextLine
from ebl.fragmentarium.application.joins_schema import JoinsSchema


def text_line_content_atf(line: TextLine) -> str:
    content_start = len(line.line_number.atf) + 1
    return line.atf[content_start:]


def manuscript_line_atf(manuscript_line: ManuscriptLine) -> str:
    line = manuscript_line.line
    line_atf = text_line_content_atf(line) if isinstance(line, TextLine) else ""
    return "\n".join(
        [line_atf, *[paratext.atf for paratext in manuscript_line.paratext]]
    ).strip()


def manuscript_line_number(manuscript_line: ManuscriptLine) -> str:
    line = manuscript_line.line
    return line.line_number.atf[:-1] if isinstance(line, TextLine) else ""


def serialize_manuscript_line(manuscript_line: ManuscriptLine) -> dict:
    return {
        "manuscriptId": manuscript_line.manuscript_id,
        "labels": [label.to_value() for label in manuscript_line.labels],
        "number": manuscript_line_number(manuscript_line),
        "atf": manuscript_line_atf(manuscript_line),
        "atfTokens": cast(dict, OneOfLineSchema().dump(manuscript_line.line))[
            "content"
        ],
        "omittedWords": list(manuscript_line.omitted_words),
    }


def create(include_documents: bool) -> Tuple[Chapter, dict]:
    references = (ReferenceFactory.build(with_document=include_documents),)
    manuscript = ManuscriptFactory.build(references=references, with_old_sigla=True)

    first_manuscript_line = ManuscriptLineFactory.build(manuscript_id=manuscript.id)
    second_manuscript_line = ManuscriptLineFactory.build(manuscript_id=manuscript.id)
    variants = (
        LineVariantFactory.build(
            manuscripts=(first_manuscript_line, second_manuscript_line),
            parallel_lines=(ParallelComposition(False, "name", LineNumber(1)),),
        ),
    )
    line = LineFactory.build(variants=variants)
    line_with_old_line_numbers = LineFactory.build(
        with_old_line_numbers=True,
        variants=(
            LineVariantFactory.build(
                manuscripts=(ManuscriptLineFactory.build(manuscript_id=manuscript.id),)
            ),
        ),
    )

    chapter = ChapterFactory.build(
        manuscripts=(manuscript,),
        uncertain_fragments=(MuseumNumber.of("K.1"),),
        lines=(line, line_with_old_line_numbers),
        colophon_lines_in_query=ChapterQueryColophonLinesFactory.build(),
    )
    dto = {
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
        "manuscripts": ApiManuscriptSchema(
            exclude=[] if include_documents else ["joins"]
        ).dump(chapter.manuscripts, many=True),
        "uncertainFragments": [str(number) for number in chapter.uncertain_fragments],
        "lines": [
            {
                "number": line.number.label,
                "oldLineNumbers": OldLineNumberSchema().dump(
                    line.old_line_numbers, many=True
                ),
                "variants": [
                    {
                        "reconstruction": "".join(
                            [
                                convert_to_atf(None, variant.reconstruction),
                                f"\n{variant.note.atf}" if variant.note else "",
                                *[
                                    f"\n{parallel_line.atf}"
                                    for parallel_line in variant.parallel_lines
                                ],
                            ]
                        ),
                        "reconstructionTokens": OneOfTokenSchema().dump(
                            variant.reconstruction, many=True
                        ),
                        "intertext": "".join(part.value for part in variant.intertext),
                        "manuscripts": [
                            serialize_manuscript_line(manuscript_line)
                            for manuscript_line in variant.manuscripts
                        ],
                    }
                    for variant in line.variants
                ],
                "isSecondLineOfParallelism": line.is_second_line_of_parallelism,
                "isBeginningOfSection": line.is_beginning_of_section,
                "translation": "\n".join(
                    translation.atf for translation in line.translation
                ),
            }
            for line in chapter.lines
        ],
        "isFilteredQuery": False,
        "colophonLinesInQuery": {"colophonLinesInQuery": {}},
    }

    return chapter, dto


def test_serialize_manuscript() -> None:
    references = (ReferenceFactory.build(with_document=True),)
    manuscript = ManuscriptFactory.build(references=references, with_old_sigla=True)
    assert ApiManuscriptSchema().dump(manuscript) == {
        "id": manuscript.id,
        "siglumDisambiguator": manuscript.siglum_disambiguator,
        "oldSigla": ApiOldSiglumSchema().dump(manuscript.old_sigla, many=True),
        "museumNumber": (
            str(manuscript.museum_number) if manuscript.museum_number else ""
        ),
        "accession": manuscript.accession,
        "periodModifier": manuscript.period_modifier.value,
        "period": manuscript.period.long_name,
        "provenance": manuscript.provenance.long_name,
        "type": manuscript.type.long_name,
        "notes": manuscript.notes,
        "colophon": manuscript.colophon.atf,
        "unplacedLines": manuscript.unplaced_lines.atf,
        "references": ApiReferenceSchema().dump(manuscript.references, many=True),
        "joins": cast(dict, JoinsSchema().dump(manuscript.joins))["fragments"],
        "isInFragmentarium": manuscript.is_in_fragmentarium,
    }


def test_deserialize_manuscript(seeded_provenance_service) -> None:
    references = (ReferenceFactory.build(with_document=False),)
    manuscript = ManuscriptFactory.build(references=references, with_old_sigla=True)
    schema = ApiManuscriptSchema(
        context={"provenance_service": seeded_provenance_service}
    )
    assert (
        schema.load(
            {
                "id": manuscript.id,
                "siglumDisambiguator": manuscript.siglum_disambiguator,
                "oldSigla": ApiOldSiglumSchema().dump(manuscript.old_sigla, many=True),
                "museumNumber": (
                    str(manuscript.museum_number) if manuscript.museum_number else ""
                ),
                "accession": manuscript.accession,
                "periodModifier": manuscript.period_modifier.value,
                "period": manuscript.period.long_name,
                "provenance": manuscript.provenance.long_name,
                "type": manuscript.type.long_name,
                "notes": manuscript.notes,
                "colophon": manuscript.colophon.atf,
                "unplacedLines": manuscript.unplaced_lines.atf,
                "references": ApiReferenceSchema().dump(
                    manuscript.references, many=True
                ),
            }
        )
        == manuscript
    )


def test_serialize() -> None:
    chapter, dto = create(True)
    assert ApiChapterSchema().dump(chapter) == dto


def test_deserialize(seeded_provenance_service) -> None:
    chapter, dto = create(False)
    del dto["lines"][0]["variants"][0]["reconstructionTokens"]
    schema = ApiChapterSchema(context={"provenance_service": seeded_provenance_service})
    assert schema.load(dto) == chapter
