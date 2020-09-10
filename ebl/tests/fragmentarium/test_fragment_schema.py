from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.tests.factories.fragment import LemmatizedFragmentFactory
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema
from ebl.fragmentarium.domain.museum_number import MuseumNumber


def test_serialization_and_deserialization():
    fragment = LemmatizedFragmentFactory.build()
    schema = FragmentSchema()
    data = schema.dump(fragment)
    assert schema.load(data) == fragment


def test_number_serialization():
    fragment = LemmatizedFragmentFactory.build()
    data = FragmentSchema().dump(fragment)
    assert data["museumNumber"] == MuseumNumberSchema().dump(fragment.number)


def test_number_deserialization():
    number = MuseumNumber.of("Z.1.b")
    fragment = FragmentSchema().load({
        **FragmentSchema().dump(LemmatizedFragmentFactory.build()),
        "museumNumber": MuseumNumberSchema().dump(number)
    })
    assert fragment.number == number
