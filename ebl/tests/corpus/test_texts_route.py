import falcon

from ebl.corpus.application.schemas import TextSchema
from ebl.corpus.domain.chapter_info import ChapterInfo
from ebl.corpus.web.chapter_info_schema import ChapterInfoSchema
from ebl.tests.corpus.support import allow_references, allow_signs
from ebl.tests.factories.corpus import ChapterFactory, TextFactory
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.transliteration.application.signs_visitor import SignsVisitor


def create_dto(text):
    return TextSchema().dump(text)


def test_get_text(client, bibliography, sign_repository, signs, text_repository):
    text = TextFactory.build(chapters=(), references=())
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
    first_text = TextFactory.build(chapters=(), references=())
    second_text = TextFactory.build(chapters=(), references=())
    text_repository.create(first_text)
    text_repository.create(second_text)

    get_result = client.simulate_get("/texts")

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == [create_dto(first_text), create_dto(second_text)]


def test_searching_texts(client, bibliography, sign_repository, signs, text_repository):
    allow_signs(signs, sign_repository)
    chapter = ChapterFactory.build()
    allow_references(chapter, bibliography)
    text_repository.create_chapter(chapter)

    get_result = client.simulate_get("/textsearch?transliteration=ku&paginationIndex=0")

    assert get_result.status == falcon.HTTP_OK
    assert get_result.json == {
        "chapterInfos": [
            ChapterInfoSchema().dump(
                ChapterInfo.of(
                    chapter,
                    TransliterationQuery(
                        string="KU", visitor=SignsVisitor(sign_repository)
                    ),
                )
            )
        ],
        "totalCount": 1,
    }
