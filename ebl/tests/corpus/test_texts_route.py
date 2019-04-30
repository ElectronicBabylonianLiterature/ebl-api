import json

import attr
import falcon
import pydash
import pytest

from ebl.auth0 import Guest
from ebl.corpus.text import (Classification, ManuscriptType, Period,
                             PeriodModifier, Provenance, Stage)
from ebl.corpus.texts import parse_text, to_dto
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.corpus import (ChapterFactory, ManuscriptFactory,
                                        TextFactory)


ANY_USER = Guest()


def create_dto(text, include_documents=False):
    return {
        **text.to_dict(include_documents),
        'chapters': [
            {
                **chapter.to_dict(include_documents),
                'lines': [
                    {
                        **line.to_dict(),
                        'manuscripts': [
                            pydash.omit({
                                **manuscript.to_dict(),
                                'atf': manuscript.line.atf
                            }, 'line') for manuscript in line.manuscripts
                        ]
                    } for line in chapter.lines
                ]
            } for chapter in text.chapters
        ]
    }


def allow_references(text, bibliography):
    for chapter in text.chapters:
        for manuscript in chapter.manuscripts:
            for reference in manuscript.references:
                bibliography.create(reference.document, ANY_USER)


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

    assert parse_text(dto) == text


def test_to_dto():
    text = TextFactory.build()
    dto = create_dto(text, True)

    assert to_dto(text) == dto


def test_created_text_can_be_fetched(client, bibliography):
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


def test_updating_text(client, bibliography):
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


def test_updating_invalid_reference(client, bibliography):
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
                    'period': Period.OLD_ASSYRIAN.value,
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
                    'period': Period.OLD_ASSYRIAN.value,
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


@pytest.mark.parametrize("updated_text,expected_status", [
    [create_dto(TextFactory.build(category='invalid')),
     falcon.HTTP_BAD_REQUEST],
    [create_dto(TextFactory.build(chapters=(ChapterFactory.build(name=''),))),
     falcon.HTTP_BAD_REQUEST],
    [INVALID_MANUSCRIPTS, falcon.HTTP_UNPROCESSABLE_ENTITY],
])
def test_update_text_invalid_entity(client,
                                    bibliography,
                                    updated_text,
                                    expected_status):
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)

    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}',
        body=json.dumps(updated_text)
    )

    assert post_result.status == expected_status
