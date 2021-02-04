from typing import Tuple

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.corpus.domain.text import Text
from ebl.corpus.web.api_serializer import deserialize, serialize
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
    TextFactory,
)
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.domain.atf_visitor import convert_to_atf
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.parallel_line import ParallelComposition
from ebl.transliteration.domain.text_line import TextLine


def create(include_documents: bool) -> Tuple[Text, dict]:
    references = (
        ReferenceFactory.build(with_document=include_documents),  # pyre-ignore[16]
    )
    manuscript = ManuscriptFactory.build(references=references)  # pyre-ignore[16]
    # pyre-ignore[16]
    first_manuscript_line = ManuscriptLineFactory.build(manuscript_id=manuscript.id)
    second_manuscript_line = ManuscriptLineFactory.build(manuscript_id=manuscript.id)
    line = LineFactory.build(  # pyre-ignore[16]
        variants=(
            LineVariantFactory.build(  # pyre-ignore[16]
                manuscripts=(first_manuscript_line, second_manuscript_line),
                parallel_lines=(ParallelComposition(False, "name", LineNumber(1)),),
            ),
        )
    )
    # pyre-ignore[16]
    chapter = ChapterFactory.build(
        manuscripts=(manuscript,),
        uncertain_fragments=(MuseumNumber.of("K.1"),),
        lines=(line,),
    )
    text = TextFactory.build(chapters=(chapter,))  # pyre-ignore[16]
    dto = {
        "category": text.category,
        "index": text.index,
        "name": text.name,
        "numberOfVerses": text.number_of_verses,
        "approximateVerses": text.approximate_verses,
        "chapters": [
            {
                "classification": chapter.classification.value,
                "stage": chapter.stage.value,
                "version": chapter.version,
                "name": chapter.name,
                "order": chapter.order,
                "parserVersion": chapter.parser_version,
                "manuscripts": [
                    {
                        "id": manuscript.id,
                        "siglumDisambiguator": manuscript.siglum_disambiguator,
                        "museumNumber": str(manuscript.museum_number)
                        if manuscript.museum_number
                        else "",
                        "accession": manuscript.accession,
                        "periodModifier": manuscript.period_modifier.value,
                        "period": manuscript.period.long_name,
                        "provenance": manuscript.provenance.long_name,
                        "type": manuscript.type.long_name,
                        "notes": manuscript.notes,
                        # pyre-ignore[16]
                        "references": ApiReferenceSchema().dump(references, many=True),
                    }
                    for manuscript in chapter.manuscripts
                ],
                "uncertainFragments": [
                    str(number) for number in chapter.uncertain_fragments
                ],
                "lines": [
                    {
                        "number": line.number.label,
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
                                # pyre-ignore[16]
                                "reconstructionTokens": OneOfTokenSchema().dump(
                                    variant.reconstruction, many=True
                                ),
                                "manuscripts": [
                                    {
                                        "manuscriptId": manuscript_line.manuscript_id,
                                        "labels": [
                                            label.to_value()
                                            for label in manuscript_line.labels
                                        ],
                                        "number": manuscript_line.line.line_number.atf[
                                            :-1
                                        ]
                                        if isinstance(manuscript_line.line, TextLine)
                                        else "",
                                        "atf": "\n".join(
                                            [
                                                manuscript_line.line.atf[
                                                    len(
                                                        manuscript_line.line.line_number.atf
                                                    )
                                                    + 1 :
                                                ]
                                                if isinstance(
                                                    manuscript_line.line, TextLine
                                                )
                                                else "",
                                                *[
                                                    line.atf
                                                    for line in manuscript_line.paratext
                                                ],
                                            ]
                                        ).strip(),
                                        "atfTokens": (
                                            # pyre-ignore[16]
                                            OneOfLineSchema().dump(
                                                manuscript_line.line
                                            )["content"]
                                        ),
                                        "omittedWords": list(
                                            manuscript_line.omitted_words
                                        ),
                                    }
                                    for manuscript_line in variant.manuscripts
                                ],
                            }
                            for variant in line.variants
                        ],
                        "isSecondLineOfParallelism": line.is_second_line_of_parallelism,
                        "isBeginningOfSection": line.is_beginning_of_section,
                    }
                    for line in chapter.lines
                ],
            }
            for chapter in text.chapters
        ],
    }

    return text, dto


def test_serialize() -> None:
    text, dto = create(True)
    assert serialize(text) == dto


def test_deserialize() -> None:
    text, dto = create(False)
    del dto["chapters"][0]["lines"][0]["variants"][0]["reconstructionTokens"]
    assert deserialize(dto) == text
