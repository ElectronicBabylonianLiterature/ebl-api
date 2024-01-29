import falcon

from ebl.corpus.application.schemas import TextSchema
from ebl.tests.factories.corpus import TextFactory


def create_dto(text):
    return TextSchema().dump(text)


def test_get_text(client, bibliography, sign_repository, signs, text_repository):
    text = TextFactory.build(chapters=tuple(), references=tuple())
    text_repository.create(text)

    get_result = client.simulate_get(
        f"/texts/{text.genre.value}/{text.category}/{text.index}"
    )

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == create_dto(text)


def test_text_not_found(client):
    result = client.simulate_get("/texts/1/1")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_invalid_section(client):
    result = client.simulate_get("/texts/invalid/1")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_invalid_index(client):
    result = client.simulate_get("/texts/1/invalid")

    assert result.status == falcon.HTTP_NOT_FOUND


def test_listing_texts(client, bibliography, text_repository):
    first_text = TextFactory.build(chapters=tuple(), references=tuple())
    second_text = TextFactory.build(chapters=tuple(), references=tuple())
    text_repository.create(first_text)
    text_repository.create(second_text)

    get_result = client.simulate_get("/texts")

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == [create_dto(first_text), create_dto(second_text)]
