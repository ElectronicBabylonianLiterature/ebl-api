import attr
import pytest

from ebl.bibliography.domain.reference import BibliographyId
from ebl.tests.factories.bibliography import BibliographyEntryFactory, ReferenceFactory
from ebl.tests.factories.dossier import DossierRecordFactory


@pytest.mark.parametrize("reader", ["find_all", "query_by_ids", "search"])
def test_dossier_hydrates_legacy_bibliography_without_rewriting_references(
    dossiers_repository, bibliography_repository, reader
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
    dossier = DossierRecordFactory.build(id="alias-dossier", references=references)
    dossiers_repository.create(dossier)
    if reader == "find_all":
        result = dossiers_repository.find_all()
    elif reader == "query_by_ids":
        result = dossiers_repository.query_by_ids([dossier.id])
    else:
        result = dossiers_repository.search(dossier.id)

    assert result[0].references == tuple(
        attr.evolve(reference, document=canonical) for reference in references
    )


def test_dossier_omits_unresolvable_bibliography(
    dossiers_repository, bibliography_repository
):
    for id_, target in (("BROKEN", "MISSING"), ("LOOP", "LOOP")):
        bibliography_repository.create(
            BibliographyEntryFactory.build(id=id_, deprecated=True, redirectTo=target)
        )
    references = tuple(
        ReferenceFactory.build(id=BibliographyId(id_), document=None)
        for id_ in ("BROKEN", "LOOP", "UNKNOWN")
    )
    dossier = DossierRecordFactory.build(references=references)
    dossiers_repository.create(dossier)

    assert dossiers_repository.query_by_ids([dossier.id])[0].references == tuple(
        attr.evolve(reference, document={}) for reference in references
    )
