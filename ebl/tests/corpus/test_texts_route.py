import json
import attr
import falcon
import pytest
from ebl.auth0 import Guest
from ebl.corpus.text import (
    Provenance, Period, ManuscriptType, Stage, Classification
)
from ebl.tests.factories.corpus import (
    TextFactory, ChapterFactory, ManuscriptFactory
)


ANY_USER = Guest()


def allow_references(text, bibliography):
    for chapter in text.chapters:
        for manuscript in chapter.manuscripts:
            for reference in manuscript.references:
                bibliography.create(reference.document, ANY_USER)


def put_text(client, text):
    put_result = client.simulate_put(
        f'/texts',
        body=json.dumps(text.to_dict())
    )
    assert put_result.status == falcon.HTTP_NO_CONTENT
    assert put_result.headers['Access-Control-Allow-Origin'] == '*'


def test_created_text_can_be_fetched(client, bibliography):
    text = TextFactory.build()
    allow_references(text, bibliography)
    put_text(client, text)

    get_result = client.simulate_get(f'/texts/{text.category}/{text.index}')

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers['Access-Control-Allow-Origin'] == '*'
    assert get_result.json == text.to_dict(True)


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
    put_text(client, text)
    updated_text = attr.evolve(text, index=2, name='New Name')

    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}',
        body=json.dumps(updated_text.to_dict())
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'
    assert post_result.json == updated_text.to_dict(True)

    get_result = client.simulate_get(
        f'/texts/{updated_text.category}/{updated_text.index}'
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.headers['Access-Control-Allow-Origin'] == '*'
    assert get_result.json == updated_text.to_dict(True)


def test_updating_text_not_found(client, bibliography):
    text = TextFactory.build()
    allow_references(text, bibliography)

    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}',
        body=json.dumps(text.to_dict())
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_invalid_reference(client, bibliography):
    text = TextFactory.build()
    allow_references(text, bibliography)
    put_text(client, text)
    updated_text = TextFactory.build()

    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}',
        body=json.dumps(updated_text.to_dict())
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
        body=json.dumps(invalid.to_dict())
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND


def test_updating_text_invalid_id(client):
    text = TextFactory.build()

    post_result = client.simulate_post(
        f'/texts/{text.category}/invalid',
        body=json.dumps(text.to_dict())
    )

    assert post_result.status == falcon.HTTP_NOT_FOUND

DUPLICATE_MANUSCRIPTS = {
    # pylint: disable=E1101
    'category': 1,
    'index': 1,
    'name': 'name',
    'numberOfVerses': 100,
    'approximateVerses': False,
    'chapters': [
        {
            'classification': Classification.ANCIENT.value,
            'stage': Stage.OLD_ASSYRIAN.long_name,
            'name': 'I',
            'order': 0,
            'manuscripts': [
                {
                    'siglumNumber': 1,
                    'museumNumber': '',
                    'accession': '',
                    'period': Period.OLD_ASSYRIAN.long_name,
                    'provenance': Provenance.BABYLON.long_name,
                    'type': ManuscriptType.SCHOOL.long_name,
                    'references': []
                },
                {
                    'siglumNumber': 1,
                    'museumNumber': '',
                    'accession': '',
                    'period': Period.OLD_ASSYRIAN.long_name,
                    'provenance': Provenance.BABYLON.long_name,
                    'type': ManuscriptType.SCHOOL.long_name,
                    'references': []
                }
            ]
        }
    ]
}


@pytest.mark.parametrize("updated_text,expected_status", [
    [TextFactory.build(category='invalid').to_dict(), falcon.HTTP_BAD_REQUEST],
    [TextFactory.build(chapters=(
        ChapterFactory.build(name=''),
    )).to_dict(), falcon.HTTP_BAD_REQUEST],
    [DUPLICATE_MANUSCRIPTS, falcon.HTTP_UNPROCESSABLE_ENTITY],
    [TextFactory.build(chapters=(
        ChapterFactory.build(manuscripts=(
            ManuscriptFactory.build(museum_number='BM.X', accession='K.X'),
        )),
    )).to_dict(), falcon.HTTP_UNPROCESSABLE_ENTITY]
])
def test_update_text_invalid_entity(client,
                                    bibliography,
                                    updated_text,
                                    expected_status):
    text = TextFactory.build()
    allow_references(text, bibliography)
    put_text(client, text)

    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}',
        body=json.dumps(updated_text)
    )

    assert post_result.status == expected_status
