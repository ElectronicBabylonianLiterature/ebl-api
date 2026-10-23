import pytest
from marshmallow import ValidationError
from pymongo.database import Database

from ebl.common.domain.scopes import Scope
from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber


def test_strict_read_scopes_preserve_legacy_missing_lookup(
    fragment_repository: FragmentRepository,
) -> None:
    number = MuseumNumber.of("K.999")

    assert fragment_repository.fetch_scopes(number) == []
    with pytest.raises(NotFoundError, match=r"Fragment K\.999 not found\."):
        fragment_repository.query_read_scopes(number)


def test_read_scopes_use_canonical_number_and_scope_enums(
    database: Database, fragment_repository: FragmentRepository
) -> None:
    number = MuseumNumber.of("A/B C.01.a")
    fragment_repository.create(FragmentFactory.build(number=number, references=()))
    database.fragments.update_one(
        {"_id": str(number)},
        {"$set": {"authorizedScopes": ["read:CAIC", "read:URUKLBU-fragments"]}},
    )

    scopes = fragment_repository.query_read_scopes(number)

    assert scopes == [Scope.READ_CAIC_FRAGMENTS, Scope.READ_URUKLBU_FRAGMENTS]
    assert (
        scopes == fragment_repository.query_by_museum_number(number).authorized_scopes
    )
    with pytest.raises(NotFoundError):
        fragment_repository.query_read_scopes(MuseumNumber.of("A/B C.01.b"))


def test_projected_scopes_preserve_full_detail_validation(
    database: Database, fragment_repository: FragmentRepository
) -> None:
    number = MuseumNumber.of("K.1")
    fragment_repository.create(FragmentFactory.build(number=number, references=()))
    database.fragments.update_one({"_id": str(number)}, {"$set": {"notes": False}})

    assert fragment_repository.query_read_scopes(number) == []
    with pytest.raises(ValidationError):
        fragment_repository.query_by_museum_number(number)
