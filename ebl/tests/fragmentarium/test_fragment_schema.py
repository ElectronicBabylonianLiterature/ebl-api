from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.tests.factories.fragment import LemmatizedFragmentFactory, FragmentFactory


def test_serialization_and_deserialization():
    fragment = LemmatizedFragmentFactory.build()
    schema = FragmentSchema()
    data = schema.dump(fragment)
    assert schema.load(data) == fragment

def test_serialization_and_deserialization2():
    fragment = FragmentFactory.build()
    del fragment.genre
    schema = FragmentSchema()
    data = schema.dump(fragment)
    o = schema.load(data)
    assert schema.load(data) == fragment
