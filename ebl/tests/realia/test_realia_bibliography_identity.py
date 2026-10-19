import attr
import pytest

from ebl.bibliography.domain.reference import BibliographyId
from ebl.realia.infrastructure.realia_schemas import RealiaEntrySchema
from ebl.tests.factories.bibliography import BibliographyEntryFactory, ReferenceFactory
from ebl.tests.factories.realia import RealiaEntryFactory, ReallexikonEntryFactory


@pytest.mark.parametrize("reader", ["find", "find_by_realia_id", "search"])
def test_realia_and_reallexikon_hydrate_legacy_bibliography(
    realia_repository, bibliography_repository, reader
):
    canonical = BibliographyEntryFactory.build(
        id="CANONICAL",
        citationKey="citation-key",
        aliases=[{"value": "Legacy Alias", "normalizedValue": "legacy-alias"}],
    )
    bibliography_repository.create(canonical)
    bibliography_repository.create(
        BibliographyEntryFactory.build(id="OLD", deprecated=True, redirectTo="MID")
    )
    bibliography_repository.create(
        BibliographyEntryFactory.build(
            id="MID", deprecated=True, redirectTo="CANONICAL"
        )
    )
    references = tuple(
        ReferenceFactory.build(
            id=BibliographyId(id_),
            pages=str(index),
            notes=f"note {index}",
            lines_cited=("1", "2"),
            document=None,
        )
        for index, id_ in enumerate(
            ("CANONICAL", "Legacy Alias", "legacy-alias", "citation-key", "OLD")
        )
    )
    reallexikon = tuple(
        ReallexikonEntryFactory.build(reference=reference) for reference in references
    )
    entry = RealiaEntryFactory.build(
        id="alias-realia", references=references, reallexikon=reallexikon
    )
    realia_repository._realia_collection.insert_one(RealiaEntrySchema().dump(entry))
    if reader == "find":
        result = realia_repository.find(entry.id)
    elif reader == "find_by_realia_id":
        result = realia_repository.find_by_realia_id(entry.realia_id)
    else:
        result = realia_repository.search(entry.id)[0]

    assert result.references == tuple(
        attr.evolve(reference, document=canonical) for reference in references
    )
    assert [rlex.reference.id for rlex in result.reallexikon] == [
        ref.id for ref in references
    ]
    assert [rlex.reference.pages for rlex in result.reallexikon] == [
        ref.pages for ref in references
    ]
    assert all(rlex.reference.document == canonical for rlex in result.reallexikon)


def test_realia_uses_empty_documents_for_unresolvable_bibliography(
    realia_repository, bibliography_repository
):
    bibliography_repository.create(
        BibliographyEntryFactory.build(
            id="BROKEN", deprecated=True, redirectTo="MISSING"
        )
    )
    references = tuple(
        ReferenceFactory.build(id=BibliographyId(id_), document=None)
        for id_ in ("BROKEN", "UNKNOWN")
    )
    entry = RealiaEntryFactory.build(
        references=references,
        reallexikon=tuple(
            ReallexikonEntryFactory.build(reference=ref) for ref in references
        ),
    )
    realia_repository._realia_collection.insert_one(RealiaEntrySchema().dump(entry))

    result = realia_repository.find(entry.id)
    assert result.references == tuple(
        attr.evolve(ref, document={}) for ref in references
    )
    assert all(rlex.reference.document == {} for rlex in result.reallexikon)
