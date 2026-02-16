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


def test_serialization_and_deserialization():
    fragment = LemmatizedFragmentFactory.build(
        joins=Joins(
            ((Join(MuseumNumber("X", "1")),),),
        ),
        authorized_scopes=[Scope.READ_ITALIANNINEVEH_FRAGMENTS],
    )
    schema = FragmentSchema()
    data = schema.dump(fragment)
    assert schema.load(data) == fragment


def test_default_joins():
    fragment = LemmatizedFragmentFactory.build(joins=Joins())
    data = FragmentSchema(exclude=["joins"]).dump(fragment)
    assert FragmentSchema().load(data) == fragment


def test_number_serialization():
    fragment = LemmatizedFragmentFactory.build()
    data = FragmentSchema().dump(fragment)
    assert data["museumNumber"] == MuseumNumberSchema().dump(fragment.number)


def test_number_deserialization():
    number = MuseumNumber.of("Z.1.b")
    fragment = FragmentSchema().load(
        {
            **FragmentSchema().dump(LemmatizedFragmentFactory.build()),
            "museumNumber": MuseumNumberSchema().dump(number),
        }
    )
    assert fragment.number == number


def test_scope_serialization():
    fragment = FragmentFactory.build(authorized_scopes=SCOPES)
    assert FragmentSchema().dump(fragment)["authorizedScopes"] == SERIALIZED_SCOPES


def test_scope_deserialization():
    data = {
        **FragmentSchema().dump(FragmentFactory.build()),
        "authorizedScopes": SERIALIZED_SCOPES,
    }
    assert FragmentSchema().load(data).authorized_scopes == SCOPES


def test_empty_accession_serialization():
    fragment = FragmentFactory.build(accession=None)
    assert "accession" not in FragmentSchema().dump(fragment)


def test_empty_accession_deserialization():
    data = {
        **FragmentSchema().dump(FragmentFactory.build()),
        "accession": None,
    }
    assert FragmentSchema().load(data).accession is None
