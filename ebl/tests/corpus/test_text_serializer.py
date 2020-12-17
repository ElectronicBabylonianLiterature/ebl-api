from ebl.bibliography.application.reference_schema import (
    ApiReferenceSchema,
    ReferenceSchema,
)
from ebl.corpus.application.text_serializer import serialize, deserialize
from ebl.corpus.domain.text import Text
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
    TextFactory,
)
from ebl.transliteration.application.line_schemas import NoteLineSchema, TextLineSchema
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema
import attr


REFERENCES = (ReferenceFactory.build(with_document=True),)  # pyre-ignore[16]
MANUSCRIPT = ManuscriptFactory.build(references=REFERENCES)  # pyre-ignore[16]
FIRST_MANUSCRIPT_LINE = ManuscriptLineFactory.build(  # pyre-ignore[16]
    manuscript_id=MANUSCRIPT.id
)
SECOND_MANUSCRIPT_LINE = ManuscriptLineFactory.build(manuscript_id=MANUSCRIPT.id)
# pyre-ignore[16]
LINE_VARIANT = LineVariantFactory.build(
    manuscripts=(FIRST_MANUSCRIPT_LINE, SECOND_MANUSCRIPT_LINE)
)
LINE = LineFactory.build(variants=(LINE_VARIANT,))  # pyre-ignore[16]
CHAPTER = ChapterFactory.build(  # pyre-ignore[16]
    manuscripts=(MANUSCRIPT,), lines=(LINE,)
)
TEXT = TextFactory.build(chapters=(CHAPTER,))  # pyre-ignore[16]


def strip_documents(text: Text) -> Text:
    return attr.evolve(
        text,
        chapters=tuple(
            attr.evolve(
                chapter,
                manuscripts=tuple(
                    attr.evolve(
                        manuscript,
                        references=tuple(
                            attr.evolve(reference, document=None)
                            for reference in MANUSCRIPT.references
                        ),
                    )
                    for manuscript in chapter.manuscripts
                ),
            )
            for chapter in text.chapters
        ),
    )


def to_dict(text: Text, include_documents=False):
    return {
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
                        "museumNumber": (
                            (
                                str(manuscript.museum_number)
                                if manuscript.museum_number
                                else ""
                            )
                            if include_documents
                            else manuscript.museum_number
                            # pyre-ignore[16]
                            and MuseumNumberSchema().dump(manuscript.museum_number)
                        ),
                        "accession": manuscript.accession,
                        "periodModifier": manuscript.period_modifier.value,
                        "period": manuscript.period.long_name,
                        "provenance": manuscript.provenance.long_name,
                        "type": manuscript.type.long_name,
                        "notes": manuscript.notes,
                        "references": (  # pyre-ignore[16]
                            ApiReferenceSchema if include_documents else ReferenceSchema
                        )().dump(manuscript.references, many=True),
                    }
                    for manuscript in chapter.manuscripts
                ],
                "lines": [
                    {
                        "variants": [
                            {
                                # pyre-ignore[16]
                                "text": TextLineSchema().dump(variant.text),
                                "note": variant.note
                                # pyre-ignore[16]
                                and NoteLineSchema().dump(variant.note),
                                "manuscripts": [
                                    {
                                        "manuscriptId": manuscript_line.manuscript_id,
                                        "labels": [
                                            label.to_value()
                                            for label in manuscript_line.labels
                                        ],
                                        # pyre-ignore[16]
                                        "line": OneOfLineSchema().dump(
                                            manuscript_line.line
                                        ),
                                        "paratext": OneOfLineSchema().dump(
                                            manuscript_line.paratext, many=True
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


def test_serialize():
    assert serialize(TEXT) == to_dict(TEXT)


def test_deserialize():
    assert deserialize(to_dict(TEXT)) == strip_documents(TEXT)
