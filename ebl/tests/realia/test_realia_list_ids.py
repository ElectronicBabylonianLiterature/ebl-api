import pytest

from ebl.realia.application.realia_repository import RealiaRepository
from ebl.realia.infrastructure.mongo_realia_repository import MongoRealiaRepository
from ebl.tests.realia.realia_repository_helpers import insert_minimal, insert_stored

CANONICAL_CROSS_REFERENCE = {"id": "Canonical", "lemma": "Canonical"}
OTHER_CROSS_REFERENCE = {"id": "Other", "lemma": "Other"}


def _insert_with_single_cross_reference(
    realia_repository: MongoRealiaRepository, identifier: str, **fields
) -> None:
    insert_stored(
        realia_repository,
        {
            "_id": identifier,
            "crossReferences": [CANONICAL_CROSS_REFERENCE],
            **fields,
        },
    )


def test_list_non_redirect_ids_sorted(realia_repository: MongoRealiaRepository) -> None:
    for identifier in ("Pig", "Anu", "Enlil, Ellil"):
        insert_minimal(realia_repository, identifier)

    assert realia_repository.list_non_redirect_ids() == ["Anu", "Enlil, Ellil", "Pig"]


def test_list_non_redirect_ids_empty(realia_repository: RealiaRepository) -> None:
    assert realia_repository.list_non_redirect_ids() == []


def test_list_non_redirect_ids_returns_every_id_without_limit(
    realia_repository: MongoRealiaRepository,
) -> None:
    identifiers = [f"Realia {index:02d}" for index in range(25)]
    for identifier in identifiers:
        insert_minimal(realia_repository, identifier)

    assert realia_repository.list_non_redirect_ids() == sorted(identifiers)


def test_list_non_redirect_ids_ignores_case_and_accents_when_sorting(
    realia_repository: MongoRealiaRepository,
) -> None:
    for identifier in ("Zikkurat", "Ähre", "apsu", "Adad"):
        insert_minimal(realia_repository, identifier)

    assert realia_repository.list_non_redirect_ids() == [
        "Adad",
        "Ähre",
        "apsu",
        "Zikkurat",
    ]


def test_list_non_redirect_ids_orders_equivalent_ids_deterministically(
    realia_repository: MongoRealiaRepository,
) -> None:
    for identifier in ("Ähre", "Ahre"):
        insert_minimal(realia_repository, identifier)

    assert realia_repository.list_non_redirect_ids() == ["Ahre", "Ähre"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("afoRegister", [{"mainWord": "x"}]),
        ("references", [{"id": "bib_1"}]),
        ("afoCrossReferences", [{"id": "a", "lemma": "b"}]),
        ("relatedTerms", ["Schwein", "Sau"]),
        ("type", ["Divine names"]),
        ("wikidataId", ["Q787"]),
    ],
)
def test_list_non_redirect_ids_lists_entries_with_own_content(
    field: str, value: list, realia_repository: MongoRealiaRepository
) -> None:
    _insert_with_single_cross_reference(realia_repository, "Listed", **{field: value})

    assert realia_repository.list_non_redirect_ids() == ["Listed"]


@pytest.mark.parametrize(
    "reallexikon",
    [
        [{"id": "a", "reference": {"id": "bib_1"}}],
        [{"id": "a", "reference": "bib_1"}],
        [{"id": "a", "reference": None}, {"id": "b", "reference": {"id": "bib_1"}}],
    ],
)
def test_list_non_redirect_ids_lists_entries_with_resolvable_reallexikon(
    reallexikon: list, realia_repository: MongoRealiaRepository
) -> None:
    _insert_with_single_cross_reference(
        realia_repository, "Listed", reallexikon=reallexikon
    )

    assert realia_repository.list_non_redirect_ids() == ["Listed"]


@pytest.mark.parametrize(
    "reallexikon",
    [
        [{"id": "r", "reference": None}],
        [{"id": "r", "reference": {"pages": "5"}}],
        [{"id": "r", "reference": ""}],
        [{"id": "a", "reference": None}, {"id": "b", "reference": None}],
    ],
)
def test_list_non_redirect_ids_excludes_unresolvable_reallexikon(
    reallexikon: list, realia_repository: MongoRealiaRepository
) -> None:
    _insert_with_single_cross_reference(
        realia_repository, "Stub", reallexikon=reallexikon
    )

    assert realia_repository.list_non_redirect_ids() == []


def test_list_non_redirect_ids_excludes_bare_redirect_stub(
    realia_repository: MongoRealiaRepository,
) -> None:
    _insert_with_single_cross_reference(realia_repository, "Stub")

    assert realia_repository.list_non_redirect_ids() == []


def test_list_non_redirect_ids_lists_entry_with_several_cross_references(
    realia_repository: MongoRealiaRepository,
) -> None:
    insert_stored(
        realia_repository,
        {
            "_id": "Listed",
            "crossReferences": [CANONICAL_CROSS_REFERENCE, OTHER_CROSS_REFERENCE],
        },
    )

    assert realia_repository.list_non_redirect_ids() == ["Listed"]


def test_list_non_redirect_ids_lists_entry_without_cross_references(
    realia_repository: MongoRealiaRepository,
) -> None:
    insert_stored(realia_repository, {"_id": "Listed"})

    assert realia_repository.list_non_redirect_ids() == ["Listed"]
