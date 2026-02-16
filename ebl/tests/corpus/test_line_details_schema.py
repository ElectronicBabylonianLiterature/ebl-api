from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.corpus.web.chapter_schemas import ApiOldSiglumSchema
from ebl.corpus.web.display_schemas import (
    JoinDisplaySchema,
    LineDetailsDisplay,
    LineDetailsDisplaySchema,
)
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
MANUSCRIPT = ManuscriptFactory.build(
    references=REFERENCES, with_joins=True, with_old_sigla=True
)
MANUSCRIPT_LINE = ManuscriptLineFactory.build(manuscript_id=MANUSCRIPT.id)
LINE = LineFactory.build(
    variants=(
        LineVariantFactory.build(
            manuscripts=(MANUSCRIPT_LINE,),
        ),
    )
)
CHAPTER = ChapterFactory.build(manuscripts=(MANUSCRIPT,), lines=(LINE,))

LINE_DETAILS = LineDetailsDisplay.from_line_manuscripts(LINE, (MANUSCRIPT,))

SERIALIZED_LINE_DETAILS: dict = {
    "variants": [
        {
            "manuscripts": [
                {
                    "line": OneOfLineSchema().dump(MANUSCRIPT_LINE.line),
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
                    "museumNumber": (
                        str(MANUSCRIPT.museum_number)
                        if MANUSCRIPT.museum_number
                        else ""
                    ),
                    "isInFragmentarium": MANUSCRIPT.is_in_fragmentarium,
                    "accession": MANUSCRIPT.accession,
                    "joins": [
                        [JoinDisplaySchema().dump(join) for join in fragment]
                        for fragment in MANUSCRIPT.joins.fragments
                    ],
                    "omittedWords": list(MANUSCRIPT_LINE.omitted_words),
                }
            ]
        }
    ]
}


def test_serialize() -> None:
    assert LineDetailsDisplaySchema().dump(LINE_DETAILS) == SERIALIZED_LINE_DETAILS
