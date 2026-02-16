from ebl.fragmentarium.domain.fragment import Fragment
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.factories.colophon import (
    NameAttestationFactory,
    IndividualAttestationFactory,
    ColophonFactory,
)


def test_fetch_names(fragment_repository):
    names = ["barmarum", "garmarum", "harmarum", "zarmārum"]
    [name, second_name, third_name, fourth_name] = [
        NameAttestationFactory.build(value=name) for name in names
    ]
    unrelated_name = NameAttestationFactory.build(value="pallaqum")
    individuals = [
        IndividualAttestationFactory.build(
            name=name,
            son_of=second_name,
            grandson_of=unrelated_name,
            family=unrelated_name,
        ),
        IndividualAttestationFactory.build(
            name=unrelated_name,
            son_of=unrelated_name,
            grandson_of=third_name,
            family=fourth_name,
        ),
    ]
    colophon = ColophonFactory.build(individuals=individuals)
    fragment: Fragment = FragmentFactory.build(colophon=colophon)
    fragment_repository.create(fragment)
    assert names == fragment_repository.fetch_names("mar")
    assert ["pallaqum"] == fragment_repository.fetch_names("pal")
    assert [] == fragment_repository.fetch_names("ma")
