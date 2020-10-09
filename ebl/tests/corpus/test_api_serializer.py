from typing import Tuple

from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.corpus.domain.text import Text
from ebl.corpus.web.api_serializer import deserialize, serialize
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
    TextFactory,
)
from ebl.transliteration.application.line_schemas import TextLineSchema
from ebl.transliteration.domain.labels import LineNumberLabel
from ebl.transliteration.domain.atf_visitor import convert_to_atf


def create(include_documents: bool) -> Tuple[Text, dict]:
    references = (
        ReferenceFactory.build(with_document=include_documents),  # pyre-ignore[16]
    )
    manuscript = ManuscriptFactory.build(references=references)  # pyre-ignore[16]
    # pyre-ignore[16]
    manuscript_line = ManuscriptLineFactory.build(manuscript_id=manuscript.id)
    line = LineFactory.build(manuscripts=(manuscript_line,))  # pyre-ignore[16]
    # pyre-ignore[16]
    chapter = ChapterFactory.build(manuscripts=(manuscript,), lines=(line,))
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
                ],
                "lines": [
                    {
                        "number": LineNumberLabel.from_atf(line.number.atf).to_value(),
                        "reconstruction": convert_to_atf(None, line.reconstruction),
                        "reconstructionTokens": [
                            {"type": "LanguageShift", "value": "%n"},
                            {"type": "AkkadianWord", "value": "buāru"},
                            {"type": "MetricalFootSeparator", "value": "(|)"},
                            {"type": "BrokenAway", "value": "["},
                            {"type": "UnknownNumberOfSigns", "value": "..."},
                            {"type": "Caesura", "value": "||"},
                            {"type": "AkkadianWord", "value": "...]-buāru#"},
                        ],
                        "isSecondLineOfParallelism": line.is_second_line_of_parallelism,
                        "isBeginningOfSection": line.is_beginning_of_section,
                        "manuscripts": [
                            {
                                "manuscriptId": manuscript_line.manuscript_id,
                                "labels": [
                                    label.to_value() for label in manuscript_line.labels
                                ],
                                "number": manuscript_line.line.line_number.atf[:-1],
                                "atf": (
                                    manuscript_line.line.atf[
                                        len(manuscript_line.line.line_number.atf) + 1 :
                                    ]
                                ),
                                "atfTokens": (
                                    # pyre-ignore[16]
                                    TextLineSchema().dump(manuscript_line.line)[
                                        "content"
                                    ]
                                ),
                            }
                        ],
                    }
                ],
            }
        ],
    }

    return text, dto


def test_serialize() -> None:
    text, dto = create(True)
    assert serialize(text) == dto


def test_deserialize() -> None:
    text, dto = create(False)
    del dto["chapters"][0]["lines"][0]["reconstructionTokens"]
    assert deserialize(dto) == text
