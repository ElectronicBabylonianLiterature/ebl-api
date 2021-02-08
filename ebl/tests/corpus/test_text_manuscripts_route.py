import json

import attr
import falcon  # pyre-ignore[21]
import pytest  # pyre-ignore[21]

from ebl.bibliography.application.reference_schema import ReferenceSchema
from ebl.corpus.domain.manuscript import (
    ManuscriptType,
    Period,
    PeriodModifier,
    Provenance,
)
from ebl.corpus.web.api_serializer import serialize
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import TextFactory
from ebl.users.domain.user import Guest

ANY_USER = Guest()


def create_dto(text):
    return serialize(text)


def allow_references(text, bibliography):
    for chapter in text.chapters:
        for manuscript in chapter.manuscripts:
            for reference in manuscript.references:
                bibliography.create(reference.document, ANY_USER)


def allow_signs(signs, sign_list):
    for sign in signs:
        sign_list.create(sign)


def create_text(client, text):
    post_result = client.simulate_post("/texts", body=json.dumps(create_dto(text)))
    assert post_result.status == falcon.HTTP_CREATED
    assert post_result.headers["Location"] == f"/texts/{text.category}/{text.index}"
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
    assert post_result.json == create_dto(text)


def test_updating(client, bibliography, sign_repository, signs):
    uncertain_fragment = MuseumNumber.of("K.1")
    allow_signs(signs, sign_repository)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)
    updated_text = attr.evolve(
        text,
        chapters=(
            attr.evolve(
                text.chapters[0],
                manuscripts=(
                    attr.evolve(
                        text.chapters[0].manuscripts[0],
                        museum_number="new.number",
                        accession="",
                    ),
                ),
                uncertain_fragments=(uncertain_fragment,),
            ),
        ),
    )

    post_result = client.simulate_post(
        f"/texts/{text.category}/{text.index}/chapters/0/manuscripts",
        body=json.dumps(
            {
                "manuscripts": create_dto(updated_text)["chapters"][0]["manuscripts"],
                "uncertainFragments": [str(uncertain_fragment)],
            }
        ),
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers["Access-Control-Allow-Origin"] == "*"
    assert post_result.json == create_dto(updated_text)

    get_result = client.simulate_get(
        f"/texts/{updated_text.category}/{updated_text.index}"
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers["Access-Control-Allow-Origin"] == "*"
    assert get_result.json == create_dto(updated_text)


def test_updating_text_not_found(client, bibliography):
    post_result = client.simulate_post(
        "/texts/1/1/chapters/0/manuscripts",
        body=json.dumps({"manuscripts": [], "uncertainFragments": []}),
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_invalid_reference(client, bibliography, sign_repository, signs):
    allow_signs(signs, sign_repository)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)
    manuscript = {
        "id": text.chapters[0].manuscripts[0].id,
        "siglumDisambiguator": "1c",
        "museumNumber": "X.1",
        "accession": "",
        "periodModifier": PeriodModifier.NONE.value,
        "period": Period.OLD_ASSYRIAN.long_name,
        "provenance": Provenance.BABYLON.long_name,
        "type": ManuscriptType.SCHOOL.long_name,
        "notes": "",
        "references": [ReferenceSchema().dump(ReferenceFactory.build())],
    }

    post_result = client.simulate_post(
        f"/texts/{text.category}/{text.index}/chapters/0/manuscripts",
        body=json.dumps({"manuscripts": [manuscript], "uncertainFragments": []}),
    )

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_updating_text_category(client):
    post_result = client.simulate_post(
        "/texts/invalid/1/chapters/0/manuscripts",
        body=json.dumps({"manuscripts": [], "uncertainFragments": []}),
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_invalid_id(client):
    post_result = client.simulate_post(
        "/texts/1/invalid/chapters/0/manuscripts",
        body=json.dumps({"manuscripts": [], "uncertainFragments": []}),
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_invalid_chapter_index(client):
    post_result = client.simulate_post(
        "/texts/1/1/chapters/invalid/manuscripts",
        body=json.dumps({"manuscripts": [], "uncertainFragments": []}),
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


AMBIGUOUS_MANUSCRIPTS = [
    {
        "id": 1,
        "siglumDisambiguator": "1c",
        "museumNumber": "X.1",
        "accession": "",
        "periodModifier": PeriodModifier.NONE.value,
        "period": Period.OLD_ASSYRIAN.long_name,
        "provenance": Provenance.BABYLON.long_name,
        "type": ManuscriptType.SCHOOL.long_name,
        "notes": "",
        "references": [],
    },
    {
        "id": 2,
        "siglumDisambiguator": "1c",
        "museumNumber": "X.2",
        "accession": "",
        "periodModifier": PeriodModifier.NONE.value,
        "period": Period.OLD_ASSYRIAN.long_name,
        "provenance": Provenance.BABYLON.long_name,
        "type": ManuscriptType.SCHOOL.long_name,
        "notes": "",
        "references": [],
    },
]


INVALID_MUSEUM_NUMBER = [
    {
        "id": 1,
        "siglumDisambiguator": "1c",
        "museumNumber": "invalid",
        "accession": "",
        "periodModifier": PeriodModifier.NONE.value,
        "period": Period.OLD_ASSYRIAN.long_name,
        "provenance": Provenance.BABYLON.long_name,
        "type": ManuscriptType.SCHOOL.long_name,
        "notes": "",
        "references": [],
    }
]


@pytest.mark.parametrize(
    "manuscripts,expected_status",
    [
        [[{}], falcon.HTTP_BAD_REQUEST],
        [[], falcon.HTTP_UNPROCESSABLE_ENTITY],
        [AMBIGUOUS_MANUSCRIPTS, falcon.HTTP_UNPROCESSABLE_ENTITY],
        [INVALID_MUSEUM_NUMBER, falcon.HTTP_BAD_REQUEST],
        [
            {"manuscripts": [], "uncertainFragments": ["invalid"]},
            falcon.HTTP_BAD_REQUEST,
        ],
    ],
)
def test_update_invalid_entity(
    client, bibliography, manuscripts, expected_status, sign_repository, signs
):
    allow_signs(signs, sign_repository)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)

    post_result = client.simulate_post(
        f"/texts/{text.category}/{text.index}/chapters/0/manuscripts",
        body=json.dumps({"manuscripts": manuscripts, "uncertainFragments": []}),
    )

    assert post_result.status == expected_status
