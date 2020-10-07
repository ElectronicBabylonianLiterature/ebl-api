from ebl.bibliography.application.reference_schema import (
    ApiReferenceSchema,
    ReferenceSchema,
)
from ebl.corpus.application.text_serializer import TextDeserializer, TextSerializer
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
    TextFactory,
)
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.line_schemas import TextLineSchema
from ebl.transliteration.domain.atf_visitor import convert_to_atf
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema
import attr


REFERENCES = (ReferenceFactory.build(with_document=True),)  # pyre-ignore[16]
MANUSCRIPT = ManuscriptFactory.build(references=REFERENCES)  # pyre-ignore[16]
ManuscriptFactory.build(references=REFERENCES)
MANUSCRIPT_LINE = ManuscriptLineFactory.build(  # pyre-ignore[16]
    manuscript_id=MANUSCRIPT.id
)
LINE = LineFactory.build(manuscripts=(MANUSCRIPT_LINE,))  # pyre-ignore[16]
CHAPTER = ChapterFactory.build(  # pyre-ignore[16]
    manuscripts=(MANUSCRIPT,), lines=(LINE,)
)
TEXT = TextFactory.build(chapters=(CHAPTER,))  # pyre-ignore[16]
TEXT_WITHOUT_DOCUMENTS = attr.evolve(
    TEXT,
    chapters=(
        attr.evolve(
            CHAPTER,
            manuscripts=(
                attr.evolve(
                    MANUSCRIPT,
                    references=tuple(
                        attr.evolve(reference, document=None)
                        for reference in MANUSCRIPT.references
                    ),
                ),
            ),
        ),
    ),
)


def to_dict(include_documents=False):
    return {
        "category": TEXT.category,
        "index": TEXT.index,
        "name": TEXT.name,
        "numberOfVerses": TEXT.number_of_verses,
        "approximateVerses": TEXT.approximate_verses,
        "chapters": [
            {
                "classification": CHAPTER.classification.value,
                "stage": CHAPTER.stage.value,
                "version": CHAPTER.version,
                "name": CHAPTER.name,
                "order": CHAPTER.order,
                "parserVersion": CHAPTER.parser_version,
                "manuscripts": [
                    {
                        "id": MANUSCRIPT.id,
                        "siglumDisambiguator": MANUSCRIPT.siglum_disambiguator,
                        "museumNumber": (
                            str(MANUSCRIPT.museum_number)
                            if MANUSCRIPT.museum_number
                            else ""
                            if include_documents
                            else MANUSCRIPT.museum_number
                            and MuseumNumberSchema().dump(MANUSCRIPT.museum_number)
                        ),
                        "accession": MANUSCRIPT.accession,
                        "periodModifier": MANUSCRIPT.period_modifier.value,
                        "period": MANUSCRIPT.period.long_name,
                        "provenance": MANUSCRIPT.provenance.long_name,
                        "type": MANUSCRIPT.type.long_name,
                        "notes": MANUSCRIPT.notes,
                        "references": (
                            ApiReferenceSchema if include_documents else ReferenceSchema
                        )().dump(MANUSCRIPT.references, many=True),
                    }
                ],
                "lines": [
                    {
                        "number": OneOfLineNumberSchema().dump(LINE.number),
                        "reconstruction": convert_to_atf(None, LINE.reconstruction),
                        "manuscripts": [
                            {
                                "manuscriptId": MANUSCRIPT_LINE.manuscript_id,
                                "labels": [
                                    label.to_value() for label in MANUSCRIPT_LINE.labels
                                ],
                                "line": TextLineSchema().dump(MANUSCRIPT_LINE.line),
                            }
                        ],
                    }
                ],
            }
        ],
    }


def test_serializing_to_dict():
    assert TextSerializer.serialize(TEXT) == to_dict()


def test_deserialize():
    assert TextDeserializer.deserialize(to_dict()) == TEXT_WITHOUT_DOCUMENTS
