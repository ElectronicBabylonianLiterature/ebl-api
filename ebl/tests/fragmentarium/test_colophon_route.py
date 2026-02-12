import falcon
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.factories.colophon import (
    NameAttestationFactory,
    IndividualAttestationFactory,
    ColophonFactory,
)


def test_fetch_names_route(client, fragmentarium):
    names = ["barmarum", "garmarum", "harmarum", "zarmarum"]
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
    fragment = FragmentFactory.build(colophon=colophon)
    fragmentarium.create(fragment)
    expected_json = names
    get_result = client.simulate_get(
        "/fragments/colophon-names",
        params={"query": "mar"},
    )
    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == expected_json
