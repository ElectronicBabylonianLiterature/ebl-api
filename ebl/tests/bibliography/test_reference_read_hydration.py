from typing import Tuple

import attr
import pytest

from ebl.bibliography.application.partner_identity import create_partner_alias
from ebl.bibliography.domain.reference import Reference
from ebl.tests.factories.bibliography import BibliographyEntryFactory, ReferenceFactory
from ebl.tests.factories.corpus import TextFactory
from ebl.tests.factories.fragment import FragmentFactory


@pytest.fixture
def hydrated_identity_entries(bibliography_repository):
    canonical = BibliographyEntryFactory.build(
        id="CANONICAL", aliases=[create_partner_alias("ALIAS")], citationKey="CITATION"
    )
    entries = [
        canonical,
        BibliographyEntryFactory.build(
            id="OLD", deprecated=True, redirectTo="CANONICAL"
        ),
        BibliographyEntryFactory.build(id="OLDER", deprecated=True, redirectTo="OLD"),
        BibliographyEntryFactory.build(
            id="DANGLING", deprecated=True, redirectTo="ABSENT"
        ),
        BibliographyEntryFactory.build(
            id="CYCLE_A", deprecated=True, redirectTo="CYCLE_B"
        ),
        BibliographyEntryFactory.build(
            id="CYCLE_B", deprecated=True, redirectTo="CYCLE_A"
        ),
        BibliographyEntryFactory.build(
            id="AMBIGUOUS_A", aliases=[create_partner_alias("AMBIGUOUS")]
        ),
        BibliographyEntryFactory.build(
            id="AMBIGUOUS_B", aliases=[create_partner_alias("AMBIGUOUS")]
        ),
    ]
    for entry in entries:
        bibliography_repository.create(entry)
    return canonical


def occurrence_references() -> Tuple[Reference, ...]:
    return tuple(
        ReferenceFactory.build(
            id=id_,
            pages=f"{index + 1}",
            notes=f"Occurrence {index}",
            lines_cited=(f"{index + 2}",),
            document=None,
        )
        for index, id_ in enumerate(
            [
                "CANONICAL",
                "ALIAS",
                "CITATION",
                "OLD",
                "OLDER",
                "MISSING",
                "DANGLING",
                "CYCLE_A",
                "AMBIGUOUS",
                "ALIAS",
            ]
        )
    )


@pytest.mark.parametrize("reader", ["fragment", "corpus_find", "corpus_list"])
def test_reference_reads_resolve_equivalent_ids_preserving_occurrences(
    fragment_repository, text_repository, hydrated_identity_entries, reader
):
    references = occurrence_references()
    if reader == "fragment":
        source = FragmentFactory.build(references=references)
        fragment_repository.create(source)
        actual = fragment_repository.query_by_museum_number(source.number)
    else:
        source = TextFactory.build(chapters=(), references=references)
        text_repository.create(source)
        actual = (
            text_repository.find(source.id)
            if reader == "corpus_find"
            else text_repository.list()[0]
        )
    expected = tuple(
        attr.evolve(
            reference,
            document=(
                hydrated_identity_entries
                if reference.id in {"CANONICAL", "ALIAS", "CITATION", "OLD", "OLDER"}
                else None
            ),
        )
        for reference in references
    )
    assert actual.references == expected


@pytest.mark.parametrize("reader", ["fragment", "corpus_find", "corpus_list"])
def test_reference_reads_with_empty_references(
    fragment_repository, text_repository, reader
):
    if reader == "fragment":
        source = FragmentFactory.build(references=())
        fragment_repository.create(source)
        actual = fragment_repository.query_by_museum_number(source.number)
    else:
        source = TextFactory.build(chapters=(), references=())
        text_repository.create(source)
        actual = (
            text_repository.find(source.id)
            if reader == "corpus_find"
            else text_repository.list()[0]
        )
    assert actual.references == ()


def test_corpus_list_hydrates_across_texts_in_a_single_batch(
    text_repository, hydrated_identity_entries, monkeypatch
):
    references = (
        ReferenceFactory.build(id="ALIAS"),
        ReferenceFactory.build(id="OLDER"),
    )
    for index in (1, 2):
        text_repository.create(
            TextFactory.build(index=index, chapters=(), references=references)
        )
    repository = text_repository._bibliography_repository
    calls = []
    original = repository.query_by_ids

    def query_by_ids(ids):
        calls.append(list(ids))
        return original(ids)

    monkeypatch.setattr(repository, "query_by_ids", query_by_ids)
    result = text_repository.list()
    assert len(result) == 2
    assert calls == [["ALIAS", "OLDER"], ["OLD"]]
    assert all(
        reference.document == hydrated_identity_entries
        for text in result
        for reference in text.references
    )
