from ebl.corpus.application.text_serializer import TextSerializer
from ebl.tests.factories.bibliography import ReferenceWithDocumentFactory
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
    TextFactory,
)
from ebl.transliteration.domain.line_schemas import dump_line

REFERENCES = (ReferenceWithDocumentFactory.build(),)
MANUSCRIPT = ManuscriptFactory.build(references=REFERENCES)
MANUSCRIPT_LINE = ManuscriptLineFactory.build()
LINE = LineFactory.build(manuscripts=(MANUSCRIPT_LINE,))
CHAPTER = ChapterFactory.build(manuscripts=(MANUSCRIPT,), lines=(LINE,))
TEXT = TextFactory.build(chapters=(CHAPTER,))


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
                        "references": [
                            reference.to_dict(include_documents)
                            for reference in REFERENCES
                        ],
                    }
                ],
                "lines": [
                    {
                        "number": LINE.number.to_value(),
                        "reconstruction": " ".join(
                            str(token) for token in LINE.reconstruction
                        ),
                        "manuscripts": [
                            {
                                "manuscriptId": MANUSCRIPT_LINE.manuscript_id,
                                "labels": [
                                    label.to_value() for label in MANUSCRIPT_LINE.labels
                                ],
                                "line": dump_line(MANUSCRIPT_LINE.line),
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
