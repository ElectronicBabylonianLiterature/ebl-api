import json

import falcon

from ebl.auth0 import Guest
from ebl.corpus.api_serializer import serialize
from ebl.tests.factories.corpus import TextFactory

ANY_USER = Guest()


def create_dto(text, include_documents=False):
    return serialize(text, include_documents)


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


def test_updating_alignment(client, bibliography, sign_list, signs):
    allow_signs(signs, sign_list)
    text = TextFactory.build()
    allow_references(text, bibliography)
    create_text(client, text)
    chapter_index = 0
    dto = {
        'alignment': [
            [
                {
                    'value': '-ku]-nu-ši',
                    'alignment': 0,
                    'hasApparatusEntry': True
                }
            ]
        ]
    }

    post_result = client.simulate_post(
        f'/texts/{text.category}/{text.index}'
        f'/chapters/{chapter_index}/alignment',
        body=json.dumps(dto)
    )

    assert post_result.status == falcon.HTTP_OK
    assert post_result.headers['Access-Control-Allow-Origin'] == '*'
    assert post_result.json == create_dto(text, True)

    get_result = client.simulate_get(
        f'/texts/{text.category}/{text.index}'
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == create_dto(text, True)
