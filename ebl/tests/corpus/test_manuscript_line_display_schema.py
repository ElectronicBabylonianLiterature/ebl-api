from ebl.corpus.application.schemas import OldSiglumSchema
from ebl.corpus.domain.manuscript import OldSiglum
from ebl.corpus.web.chapter_schemas import ApiOldSiglumSchema
from ebl.corpus.web.display_schemas import ManuscriptLineDisplaySchema
from ebl.tests.bibliography.test_reference import create_reference_with_document
from ebl.tests.factories.corpus import ChapterFactory, OldSiglumFactory
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
    line = chapter.lines[0].variants[0].manuscripts[0]
    manuscript = chapter.get_manuscript(line.manuscript_id)
    MANUSCRIPTS_BY_ID = {m.id: m for m in chapter.manuscripts}
    schema = ManuscriptLineDisplaySchema(context={"manuscripts": MANUSCRIPTS_BY_ID})

    assert schema.dump(line) == {
        "siglumDisambiguator": manuscript.siglum_disambiguator,
        "oldSigla": ApiOldSiglumSchema().dump(manuscript.old_sigla, many=True),
        "periodModifier": manuscript.period_modifier.value,
        "period": manuscript.period.long_name,
        "provenance": manuscript.provenance.long_name,
        "type": manuscript.type.long_name,
        "labels": [label.to_value() for label in line.labels],
        "line": OneOfLineSchema().dump(line.line),
        "paratext": OneOfLineSchema().dump(line.paratext, many=True),
        "references": ApiReferenceSchema().dump(manuscript.references, many=True),
    }
