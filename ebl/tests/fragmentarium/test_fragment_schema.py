from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.tests.factories.fragment import LemmatizedFragmentFactory


def test_serialization_and_deserialization():
    fragment = LemmatizedFragmentFactory.build()
    schema = FragmentSchema()
    data = schema.dump(fragment)
    assert schema.load(data) == fragment
