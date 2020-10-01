from ebl.bibliography.application.reference_schema import (
    ApiReferenceSchema,
    ReferenceSchema,
)
from ebl.corpus.application.text_serializer import TextDeserializer, TextSerializer
from ebl.tests.factories.bibliography import ReferenceWithDocumentFactory
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
    TextFactory,
)
from ebl.transliteration.application.line_number_schemas import OneOfLineNumberSchema
from ebl.transliteration.application.line_schemas import TextLineSchema


REFERENCES = (ReferenceWithDocumentFactory.build(),)  # pyre-ignore[16]
MANUSCRIPT = ManuscriptFactory.build(references=REFERENCES)  # pyre-ignore[16]
MANUSCRIPT_LINE = ManuscriptLineFactory.build()  # pyre-ignore[16]
LINE = LineFactory.build(manuscripts=(MANUSCRIPT_LINE,))  # pyre-ignore[16]
CHAPTER = ChapterFactory.build(  # pyre-ignore[16]
    manuscripts=(MANUSCRIPT,), lines=(LINE,)
)
TEXT = TextFactory.build(chapters=(CHAPTER,))  # pyre-ignore[16]


def to_dict(include_documents):
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
                        "museumNumber": MANUSCRIPT.museum_number,
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
                        "reconstruction": " ".join(
                            token.value for token in LINE.reconstruction
                        ),
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
    assert TextSerializer.serialize(TEXT, False) == to_dict(False)


def test_serializing_to_dict_with_documents():
    assert TextSerializer.serialize(TEXT, True) == to_dict(True)


def test_deserialize():
    assert TextDeserializer.deserialize(to_dict(True)) == TEXT
