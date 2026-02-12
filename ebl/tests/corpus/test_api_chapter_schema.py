from typing import Tuple

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.corpus.application.record_schemas import RecordSchema
from ebl.corpus.web.chapter_schemas import (
    ApiChapterSchema,
    ApiManuscriptSchema,
    ApiOldSiglumSchema,
)
from ebl.corpus.domain.chapter import Chapter
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
    ChapterQueryColophonLinesFactory,
)
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.application.line_number_schemas import OldLineNumberSchema
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.atf_visitor import convert_to_atf
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.parallel_line import ParallelComposition
from ebl.fragmentarium.application.joins_schema import JoinsSchema


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
                            {
                                "manuscriptId": manuscript_line.manuscript_id,
                                "labels": [
                                    label.to_value() for label in manuscript_line.labels
                                ],
                                "number": (
                                    ""
                                    if manuscript_line.is_empty
                                    else manuscript_line.line.line_number.atf[:-1]
                                ),
                                "atf": "\n".join(
                                    [
                                        (
                                            ""
                                            if manuscript_line.is_empty
                                            else manuscript_line.line.atf[
                                                len(
                                                    manuscript_line.line.line_number.atf
                                                )
                                                + 1 :
                                            ]
                                        ),
                                        *[
                                            line.atf
                                            for line in manuscript_line.paratext
                                        ],
                                    ]
                                ).strip(),
                                "atfTokens": OneOfLineSchema().dump(
                                    manuscript_line.line
                                )["content"],
                                "omittedWords": list(manuscript_line.omitted_words),
                            }
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
        "joins": JoinsSchema().dump(manuscript.joins)["fragments"],
        "isInFragmentarium": manuscript.is_in_fragmentarium,
    }


def test_deserialize_manuscript() -> None:
    references = (ReferenceFactory.build(with_document=False),)
    manuscript = ManuscriptFactory.build(references=references, with_old_sigla=True)
    assert (
        ApiManuscriptSchema().load(
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


def test_deserialize() -> None:
    chapter, dto = create(False)
    del dto["lines"][0]["variants"][0]["reconstructionTokens"]
    assert ApiChapterSchema().load(dto) == chapter
