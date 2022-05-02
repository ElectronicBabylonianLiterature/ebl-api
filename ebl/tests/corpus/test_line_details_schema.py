from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.corpus.application.schemas import ManuscriptLineSchema
from ebl.corpus.domain.line import ManuscriptLine
from ebl.corpus.web.chapter_schemas import ApiManuscriptSchema, ApiOldSiglumSchema
from ebl.corpus.web.display_schemas import LineDetails, LineDetailsSchema
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import (
    ChapterFactory,
    LineFactory,
    LineVariantFactory,
    ManuscriptFactory,
    ManuscriptLineFactory,
)
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema

REFERENCES = (ReferenceFactory.build(with_document=True),)
MANUSCRIPT = ManuscriptFactory.build(references=REFERENCES)
MANUSCRIPT_LINE = ManuscriptLineFactory.build(manuscript_id=MANUSCRIPT.id)
LINE = LineFactory.build(
    variants=(
        LineVariantFactory.build(
            manuscripts=(MANUSCRIPT_LINE,),
        ),
    )
)
CHAPTER = ChapterFactory.build(manuscripts=(MANUSCRIPT,), lines=(LINE,))

LINE_DETAILS = LineDetails.from_line_manuscripts(LINE, (MANUSCRIPT,))

SERIALIZED_LINE_DETAILS: dict = {
    "variants": [
        {
            "manuscripts": [
                {
                    "line": OneOfLineSchema().dump(MANUSCRIPT_LINE.line),
                    "manuscript": ApiManuscriptSchema().dump(MANUSCRIPT),
                    "oldSigla": ApiOldSiglumSchema().dump(
                        MANUSCRIPT.old_sigla, many=True
                    ),
                    "references": ApiReferenceSchema().dump(
                        MANUSCRIPT.references, many=True
                    ),
                    "siglumDisambiguator": MANUSCRIPT.siglum_disambiguator,
                    "periodModifier": MANUSCRIPT.period_modifier.value,
                    "period": MANUSCRIPT.period.long_name,
                    "provenance": MANUSCRIPT.provenance.long_name,
                    "type": MANUSCRIPT.type.long_name,
                    "labels": [label.to_value() for label in MANUSCRIPT_LINE.labels],
                    "paratext": OneOfLineSchema().dump(
                        MANUSCRIPT_LINE.paratext, many=True
                    ),
                }
            ]
        }
    ]
}


def test_serialize() -> None:
    assert LineDetailsSchema().dump(LINE_DETAILS) == SERIALIZED_LINE_DETAILS
