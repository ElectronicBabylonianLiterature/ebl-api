import pytest
from ebl.common.domain.scopes import Scope
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.fragmentarium.domain.joins import Join, Joins
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.factories.fragment import FragmentFactory, LemmatizedFragmentFactory

SCOPES = [
    Scope.READ_ITALIANNINEVEH_FRAGMENTS,
    Scope.READ_SIPPARLIBRARY_FRAGMENTS,
]
SERIALIZED_SCOPES = [
    "read:ITALIANNINEVEH-fragments",
    "read:SIPPARLIBRARY-fragments",
]


@pytest.fixture
def fragment_schema(seeded_provenance_service) -> FragmentSchema:
    return FragmentSchema(context={"provenance_service": seeded_provenance_service})


def test_serialization_and_deserialization(fragment_schema):
    fragment = LemmatizedFragmentFactory.build(
        joins=Joins(
            ((Join(MuseumNumber("X", "1")),),),
        ),
        authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS],
    )
    data = fragment_schema.dump(fragment)
    assert fragment_schema.load(data) == fragment


def test_default_joins(seeded_provenance_service):
    fragment = LemmatizedFragmentFactory.build(joins=Joins())
    data = FragmentSchema(
        exclude=["joins"],
        context={"provenance_service": seeded_provenance_service},
    ).dump(fragment)
    assert (
        FragmentSchema(context={"provenance_service": seeded_provenance_service}).load(
            data
        )
        == fragment
    )


def test_number_serialization(fragment_schema):
    fragment = LemmatizedFragmentFactory.build()
    data = fragment_schema.dump(fragment)
    assert data["museumNumber"] == MuseumNumberSchema().dump(fragment.number)


def test_number_deserialization(fragment_schema):
    number = MuseumNumber.of("Z.1.b")
    fragment = fragment_schema.load(
        {
            **fragment_schema.dump(LemmatizedFragmentFactory.build()),
            "museumNumber": MuseumNumberSchema().dump(number),
        }
    )
    assert fragment.number == number


def test_scope_serialization(fragment_schema):
    fragment = FragmentFactory.build(authorized_scopes=SCOPES)
    assert fragment_schema.dump(fragment)["authorizedScopes"] == SERIALIZED_SCOPES


def test_scope_deserialization(fragment_schema):
    data = {
        **fragment_schema.dump(FragmentFactory.build()),
        "authorizedScopes": SERIALIZED_SCOPES,
    }
    assert fragment_schema.load(data).authorized_scopes == SCOPES


def test_empty_accession_serialization(fragment_schema):
    fragment = FragmentFactory.build(accession=None)
    assert "accession" not in fragment_schema.dump(fragment)


def test_empty_accession_deserialization(fragment_schema):
    data = {
        **fragment_schema.dump(FragmentFactory.build()),
        "accession": None,
    }
    assert fragment_schema.load(data).accession is None
