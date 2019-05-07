import json

import attr
import falcon
import pytest

from ebl.auth0 import Guest
from ebl.corpus.enums import Classification, ManuscriptType, Provenance, \
    PeriodModifier, Period, Stage
from ebl.corpus.api_serializer import deserialize, ApiSerializer, serialize
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import (ChapterFactory, ManuscriptFactory,
                                        TextFactory)

ANY_USER = Guest()


def create_dto(text, include_documents=False):
    return ApiSerializer.serialize(text, include_documents)


def allow_references(text, bibliography):
    for chapter in text.chapters:
        for manuscript in chapter.manuscripts:
            for reference in manuscript.references:
                bibliography.create(reference.document, ANY_USER)


def allow_signs(signs, sign_list):
    for sign in signs:
        sign_list.create(sign)


def create_text(client, text):
    post_result = client.simulate_post(
        f'/texts',
        body=json.dumps(create_dto(text))
    )
    assert post_result.status == falcon.HTTP_CREATED
    assert post_result.headers['Location'] ==\
        f'/texts/{text.category}/{text.index}'
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'
    assert post_result.json == create_dto(text, True)


def test_parse_text():
    text = TextFactory.build(chapters=(
        ChapterFactory.build(manuscripts=(
            ManuscriptFactory.build(references=(
                ReferenceFactory.build(),
            )),
        )),
    ))
    dto = create_dto(text)

    assert deserialize(dto) == text


def test_to_dto():
    text = TextFactory.build()
    dto = create_dto(text, True)

    assert serialize(text) == dto


def test_created_text_can_be_fetched(client, bibliography, sign_list, signs):
    allow_signs(signs, sign_list)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)

    get_result = client.simulate_get(f'/texts/{text.category}/{text.index}')

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers['Access-Control-Allow-Origin'] == '*'
    assert get_result.json == create_dto(text, True)


def test_text_not_found(client):
    result = client.simulate_get('/texts/1/1')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_invalid_section(client):
    result = client.simulate_get('/texts/invalid/1')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_invalid_index(client):
    result = client.simulate_get('/texts/1/invalid')

    assert result.status == falcon.HTTP_NOT_FOUND


def test_updating_text(client, bibliography, sign_list, signs):
    allow_signs(signs, sign_list)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)
    updated_text = attr.evolve(text, index=2, name='New Name')

    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}',
        body=json.dumps(create_dto(updated_text))
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'
    assert post_result.json == create_dto(updated_text, True)

    get_result = client.simulate_get(
        f'/texts/{updated_text.category}/{updated_text.index}'
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers['Access-Control-Allow-Origin'] == '*'
    assert get_result.json == create_dto(updated_text, True)


def test_updating_text_not_found(client, bibliography):
    text = TextFactory.build()
    allow_references(text, bibliography)

    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}',
        body=json.dumps(create_dto(text))
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_invalid_reference(client, bibliography, sign_list, signs):
    allow_signs(signs, sign_list)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)
    updated_text = TextFactory.build()

    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}',
        body=json.dumps(create_dto(updated_text))
    )

    assert post_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY


def test_updating_text_invalid_category(client):
    text = TextFactory.build(chapters=(
        ChapterFactory.build(manuscripts=(
            ManuscriptFactory.build(references=tuple()),
        )),
    ))
    invalid = TextFactory.build(chapters=(
        ChapterFactory.build(manuscripts=(
            ManuscriptFactory.build(),
        )),
    ))

    post_result = client.simulate_post(
        f'/texts/invalid/{text.index}',
        body=json.dumps(create_dto(invalid))
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_text_invalid_id(client):
    text = TextFactory.build()

    post_result = client.simulate_post(
        f'/texts/{text.category}/invalid',
        body=json.dumps(create_dto(text))
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


INVALID_MANUSCRIPTS = {
    # pylint: disable=E1101
    'category': 1,
    'index': 1,
    'name': 'name',
    'numberOfVerses': 100,
    'approximateVerses': False,
    'chapters': [
        {
            'classification': Classification.ANCIENT.value,
            'stage': Stage.OLD_ASSYRIAN.value,
            'version': 'A',
            'name': 'I',
            'order': 0,
            'manuscripts': [
                {
                    'id': 1,
                    'siglumDisambiguator': '1c',
                    'museumNumber': 'X.1',
                    'accession': '',
                    'periodModifier': PeriodModifier.NONE.value,
                    'period': Period.OLD_ASSYRIAN.long_name,
                    'provenance': Provenance.BABYLON.long_name,
                    'type': ManuscriptType.SCHOOL.long_name,
                    'notes': '',
                    'references': []
                },
                {
                    'id': 2,
                    'siglumDisambiguator': '1c',
                    'museumNumber': 'X.2',
                    'accession': '',
                    'periodModifier': PeriodModifier.NONE.value,
                    'period': Period.OLD_ASSYRIAN.long_name,
                    'provenance': Provenance.BABYLON.long_name,
                    'type': ManuscriptType.SCHOOL.long_name,
                    'notes': '',
                    'references': []
                }
            ],
            'lines': []
        }
    ]
}


INVALID_SIGNS = {
    # pylint: disable=E1101
    'category': 1,
    'index': 1,
    'name': 'name',
    'numberOfVerses': 100,
    'approximateVerses': False,
    'chapters': [
        {
            'classification': Classification.ANCIENT.value,
            'stage': Stage.OLD_ASSYRIAN.value,
            'version': 'A',
            'name': 'I',
            'order': 0,
            'manuscripts': [
                {
                    'id': 1,
                    'siglumDisambiguator': '1c',
                    'museumNumber': 'X.1',
                    'accession': '',
                    'periodModifier': PeriodModifier.NONE.value,
                    'period': Period.OLD_ASSYRIAN.long_name,
                    'provenance': Provenance.BABYLON.long_name,
                    'type': ManuscriptType.SCHOOL.long_name,
                    'notes': '',
                    'references': []
                }
            ],
            'lines': [{
                'number': '1',
                'reconstruction': 'foo',
                'manuscripts': [{
                    'manuscriptId': 1,
                    'labels': [],
                    'number': '1',
                    'atf': 'xxx'
                }]
            }]
        }
    ]
}


@pytest.mark.parametrize("updated_text,expected_status", [
    [create_dto(TextFactory.build(category='invalid')),
     falcon.HTTP_BAD_REQUEST],
    [create_dto(TextFactory.build(chapters=(ChapterFactory.build(name=''),))),
     falcon.HTTP_BAD_REQUEST],
    [INVALID_MANUSCRIPTS, falcon.HTTP_UNPROCESSABLE_ENTITY],
    [INVALID_SIGNS, falcon.HTTP_UNPROCESSABLE_ENTITY]
])
def test_update_text_invalid_entity(client,
                                    bibliography,
                                    updated_text,
                                    expected_status,
                                    sign_list,
                                    signs):
    # pylint: disable=R0913
    allow_signs(signs, sign_list)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)

    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}',
        body=json.dumps(updated_text)
    )

    assert post_result.status == expected_status
