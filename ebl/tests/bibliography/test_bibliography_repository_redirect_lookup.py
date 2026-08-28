from ebl.tests.factories.bibliography import BibliographyEntryFactory


def test_query_by_redirect_target_finds_a_direct_predecessor(bibliography_repository):
    target = BibliographyEntryFactory.build(id="Q30000001")
    tombstone = BibliographyEntryFactory.build(
        id="Q30000002", deprecated=True, redirectTo="Q30000001"
    )
    bibliography_repository.create(target)
    bibliography_repository.create(tombstone)

    predecessors = bibliography_repository.query_by_redirect_target("Q30000001")

    assert [predecessor["id"] for predecessor in predecessors] == ["Q30000002"]


def test_query_by_redirect_target_is_empty_with_no_predecessors(
    bibliography_repository,
):
    live_entry = BibliographyEntryFactory.build(id="Q30000003")
    bibliography_repository.create(live_entry)

    assert bibliography_repository.query_by_redirect_target("Q30000003") == []


def test_query_by_redirect_target_finds_every_direct_predecessor(
    bibliography_repository,
):
    target = BibliographyEntryFactory.build(id="Q30000004")
    first = BibliographyEntryFactory.build(
        id="Q30000005", deprecated=True, redirectTo="Q30000004"
    )
    second = BibliographyEntryFactory.build(
        id="Q30000006", deprecated=True, redirectTo="Q30000004"
    )
    bibliography_repository.create(target)
    bibliography_repository.create(first)
    bibliography_repository.create(second)

    predecessors = {
        predecessor["id"]
        for predecessor in bibliography_repository.query_by_redirect_target("Q30000004")
    }

    assert predecessors == {"Q30000005", "Q30000006"}
