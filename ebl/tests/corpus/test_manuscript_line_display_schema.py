from ebl.corpus.application.schemas import OldSiglumSchema, ManuscriptLineSchema
from ebl.corpus.domain.manuscript import OldSiglum
from ebl.corpus.web.chapter_schemas import ApiManuscriptSchema, ApiOldSiglumSchema
from ebl.corpus.web.display_schemas import (
    ManuscriptLineDisplay,
    ManuscriptLineDisplaySchema,
)
from ebl.tests.bibliography.test_reference import create_reference_with_document
from ebl.tests.factories.corpus import ChapterFactory
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.bibliography.application.reference_schema import ApiReferenceSchema
from ebl.bibliography.domain.reference import BibliographyId, Reference, ReferenceType
from ebl.tests.factories.bibliography import BibliographyEntryFactory

ID = BibliographyId("RN.1")
TYPE: ReferenceType = ReferenceType.EDITION
PAGES = "1-6"
NOTES = "some notes"
LINES_CITED = ("o. 1", "r. iii! 2a.2", "9'")

REFERENCE = Reference(ID, TYPE, PAGES, NOTES, LINES_CITED)

SERIALIZED_REFERENCE: dict = {
    "id": ID,
    "type": TYPE.name,
    "pages": PAGES,
    "notes": NOTES,
    "linesCited": list(LINES_CITED),
}


def test_old_siglum_schema() -> None:
    old_siglum = OldSiglum("siglum_string", REFERENCE)

    serialized = {"reference": SERIALIZED_REFERENCE, "siglum": old_siglum.siglum}

    assert OldSiglumSchema().dump(old_siglum) == serialized
    assert OldSiglumSchema().load(serialized) == old_siglum


def test_api_old_siglum_schema() -> None:
    bibliography_entry = BibliographyEntryFactory.build()
    reference_with_document = create_reference_with_document(bibliography_entry)
    old_siglum_with_document = OldSiglum("siglum_string", reference_with_document)

    serialized = {
        "reference": {
            **SERIALIZED_REFERENCE,
            "id": reference_with_document.id,
            "document": bibliography_entry,
        },
        "siglum": old_siglum_with_document.siglum,
    }

    assert ApiOldSiglumSchema().dump(old_siglum_with_document) == serialized
    assert ApiOldSiglumSchema().load(serialized) == old_siglum_with_document


def test_serialize():
    chapter = ChapterFactory.build()
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
        "manuscript": ApiManuscriptSchema().dump(manuscript),
    }
