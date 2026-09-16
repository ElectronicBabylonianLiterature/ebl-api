import pytest

from ebl.realia.infrastructure.mongo_realia_repository import MongoRealiaRepository
from ebl.realia.infrastructure.realia_document_shape import ARRAY_FIELDS
from ebl.realia.infrastructure.realia_stub_filter import OWN_CONTENT_ARRAY_FIELDS
from ebl.tests.realia.realia_repository_helpers import insert_stored

CANONICAL_CROSS_REFERENCE = {"id": "Canonical", "lemma": "Canonical"}
HEALTHY_IDENTIFIER = "Anu"

NON_ARRAY_VALUES = ["a string", 7, {"id": "a"}, True]


def _insert_healthy_entry(realia_repository: MongoRealiaRepository) -> None:
    insert_stored(
        realia_repository,
        {"_id": HEALTHY_IDENTIFIER, "crossReferences": [], "type": ["Divine names"]},
    )


def _insert_redirect_shaped(
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


@pytest.mark.parametrize("field", OWN_CONTENT_ARRAY_FIELDS)
@pytest.mark.parametrize("value", NON_ARRAY_VALUES)
def test_non_array_own_content_field_does_not_break_listing(
    field: str, value: object, realia_repository: MongoRealiaRepository
) -> None:
    _insert_healthy_entry(realia_repository)
    _insert_redirect_shaped(realia_repository, "Legacy", **{field: value})

    assert realia_repository.list_non_redirect_ids() == [HEALTHY_IDENTIFIER]


@pytest.mark.parametrize("value", NON_ARRAY_VALUES)
def test_non_array_reallexikon_does_not_break_listing(
    value: object, realia_repository: MongoRealiaRepository
) -> None:
    _insert_healthy_entry(realia_repository)
    _insert_redirect_shaped(realia_repository, "Legacy", reallexikon=value)

    assert realia_repository.list_non_redirect_ids() == [HEALTHY_IDENTIFIER]


@pytest.mark.parametrize("value", NON_ARRAY_VALUES)
def test_non_array_cross_references_does_not_break_listing(
    value: object, realia_repository: MongoRealiaRepository
) -> None:
    _insert_healthy_entry(realia_repository)
    insert_stored(realia_repository, {"_id": "Legacy", "crossReferences": value})

    assert realia_repository.list_non_redirect_ids() == [HEALTHY_IDENTIFIER]


@pytest.mark.parametrize("field", ARRAY_FIELDS)
@pytest.mark.parametrize("value", NON_ARRAY_VALUES)
def test_malformed_entries_are_never_listed(
    field: str, value: object, realia_repository: MongoRealiaRepository
) -> None:
    _insert_healthy_entry(realia_repository)
    insert_stored(realia_repository, {"_id": "Legacy", field: value})

    assert realia_repository.list_non_redirect_ids() == [HEALTHY_IDENTIFIER]


def test_missing_fields_do_not_break_listing(
    realia_repository: MongoRealiaRepository,
) -> None:
    insert_stored(realia_repository, {"_id": "Bare"})

    assert realia_repository.list_non_redirect_ids() == ["Bare"]


@pytest.mark.parametrize("field", OWN_CONTENT_ARRAY_FIELDS)
def test_null_own_content_field_does_not_break_listing(
    field: str, realia_repository: MongoRealiaRepository
) -> None:
    _insert_healthy_entry(realia_repository)
    _insert_redirect_shaped(realia_repository, "Legacy", **{field: None})

    assert realia_repository.list_non_redirect_ids() == [HEALTHY_IDENTIFIER]
