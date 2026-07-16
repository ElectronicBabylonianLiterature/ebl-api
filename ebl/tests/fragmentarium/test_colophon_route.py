import json

import falcon
from ebl.fragmentarium.application.colophon_schema import ColophonSchema
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.tests.factories.fragment import FragmentFactory
from ebl.tests.factories.colophon import (
    NameAttestationFactory,
    IndividualAttestationFactory,
    ColophonFactory,
)


def test_update_colophon(client, fragmentarium, user):
    fragment = FragmentFactory.build()
    fragment_number = fragmentarium.create(fragment)
    colophon = ColophonFactory.build()
    updates = {"colophon": ColophonSchema().dump(colophon)}

    post_result = client.simulate_post(
        f"/fragments/{fragment_number}/colophon", body=json.dumps(updates)
    )

    expected_json = create_response_dto(
        fragment.set_colophon(colophon), user, fragment.number == "K.1", []
    )
    assert post_result.status == falcon.HTTP_OK
    assert post_result.json == expected_json
    assert post_result.json["realiaInfo"] == []

    get_result = client.simulate_get(f"/fragments/{fragment_number}")
    assert get_result.json == expected_json


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
