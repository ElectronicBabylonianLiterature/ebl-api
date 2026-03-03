from ebl.corpus.application.schemas import OldSiglumSchema
from ebl.corpus.domain.manuscript import OldSiglum
from ebl.corpus.web.chapter_schemas import ApiOldSiglumSchema
from ebl.corpus.web.display_schemas import (
    JoinDisplaySchema,
    ManuscriptLineDisplay,
    ManuscriptLineDisplaySchema,
)

from ebl.tests.factories.corpus import ChapterFactory, ManuscriptFactory
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.bibliography.application.reference_schema import (
    ApiReferenceSchema,
    ReferenceSchema,
)
from ebl.bibliography.domain.reference import BibliographyId, Reference, ReferenceType
from ebl.tests.factories.bibliography import BibliographyEntryFactory

ID = BibliographyId("RN.1")
TYPE: ReferenceType = ReferenceType.EDITION
PAGES = "1-6"
NOTES = "some notes"
LINES_CITED = ("o. 1", "r. iii! 2a.2", "9'")
BIBLIOGRAPHY_ENTRY = BibliographyEntryFactory.build()

REFERENCE = Reference(ID, TYPE, PAGES, NOTES, LINES_CITED)
SERIALIZED_REFERENCE: dict = {
    "id": ID,
    "type": TYPE.name,
    "pages": PAGES,
    "notes": NOTES,
    "linesCited": list(LINES_CITED),
}

REFERENCE_WITH_DOCUMENT = Reference(
    BIBLIOGRAPHY_ENTRY["id"], TYPE, PAGES, NOTES, LINES_CITED, BIBLIOGRAPHY_ENTRY
)
SERIALIZED_REFERENCE_WITH_DOCUMENT: dict = {
    **SERIALIZED_REFERENCE,
    "id": REFERENCE_WITH_DOCUMENT.id,
    "document": BIBLIOGRAPHY_ENTRY,
}


def test_old_siglum_schema() -> None:
    OLD_SIGLUM = OldSiglum("siglum_string", REFERENCE)
    SERIALIZED_OLD_SIGLUM = {
        "reference": ReferenceSchema().dump(REFERENCE),
        "siglum": OLD_SIGLUM.siglum,
    }

    assert OldSiglumSchema().dump(OLD_SIGLUM) == SERIALIZED_OLD_SIGLUM
    assert OldSiglumSchema().load(SERIALIZED_OLD_SIGLUM) == OLD_SIGLUM


def test_api_old_siglum_schema() -> None:
    OLD_SIGLUM_WITH_DOCUMENT = OldSiglum("siglum_string", REFERENCE_WITH_DOCUMENT)

    SERIALIZED_OLD_SIGLUM_WITH_DOCUMENT = {
        "reference": SERIALIZED_REFERENCE_WITH_DOCUMENT,
        "siglum": OLD_SIGLUM_WITH_DOCUMENT.siglum,
    }

    assert (
        ApiOldSiglumSchema().dump(OLD_SIGLUM_WITH_DOCUMENT)
        == SERIALIZED_OLD_SIGLUM_WITH_DOCUMENT
    )
    assert (
        ApiOldSiglumSchema().load(SERIALIZED_OLD_SIGLUM_WITH_DOCUMENT)
        == OLD_SIGLUM_WITH_DOCUMENT
    )


def test_serialize() -> None:
    chapter = ChapterFactory.build(
        manuscripts=(
            ManuscriptFactory.build(id=1, references=(REFERENCE,), with_joins=True),
        )
    )
    manuscript_line = chapter.lines[0].variants[0].manuscripts[0]
    manuscript = chapter.get_manuscript(manuscript_line.manuscript_id)
    manuscript_line_display = ManuscriptLineDisplay.from_manuscript_line(
        manuscript, manuscript_line
    )
    schema = ManuscriptLineDisplaySchema()

    assert schema.dump(manuscript_line_display) == {
        "siglumDisambiguator": manuscript.siglum_disambiguator,
        "oldSigla": ApiOldSiglumSchema().dump(manuscript.old_sigla, many=True),
        "periodModifier": manuscript.period_modifier.value,
        "period": manuscript.period.long_name,
        "provenance": manuscript.provenance.long_name,
        "type": manuscript.type.long_name,
        "labels": [label.to_value() for label in manuscript_line.labels],
        "line": OneOfLineSchema().dump(manuscript_line.line),
        "paratext": OneOfLineSchema().dump(manuscript_line.paratext, many=True),
        "references": ApiReferenceSchema().dump(manuscript.references, many=True),
        "museumNumber": (
            str(manuscript.museum_number) if manuscript.museum_number else ""
        ),
        "isInFragmentarium": manuscript.is_in_fragmentarium,
        "accession": manuscript.accession,
        "joins": [
            [JoinDisplaySchema().dump(join) for join in fragment]
            for fragment in manuscript.joins.fragments
        ],
        "omittedWords": list(manuscript_line.omitted_words),
    }
