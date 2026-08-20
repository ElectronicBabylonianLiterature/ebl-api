import pytest

from ebl.corpus.domain.chapter import ChapterId
from ebl.transliteration.domain.text_id import TextId
from ebl.errors import NotFoundError
from ebl.transliteration.domain.genre import Genre
from ebl.common.domain.stage import Stage

TEXT_ID = TextId(Genre.LITERATURE, 1, 99)
CHAPTER_ID = ChapterId(TEXT_ID, Stage.OLD_BABYLONIAN, "missing")


def test_corpus_text_keeps_domain_message(text_repository) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        text_repository.find(TEXT_ID)

    assert str(excinfo.value) == f"Text {TEXT_ID} not found."


def test_corpus_chapter_keeps_domain_message(text_repository) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        text_repository.find_chapter(CHAPTER_ID)

    assert str(excinfo.value) == f"Chapter {CHAPTER_ID} not found."


def test_corpus_manuscripts_keeps_domain_message(text_repository) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        text_repository.query_manuscripts_by_chapter(CHAPTER_ID)

    assert str(excinfo.value) == f"Chapter {CHAPTER_ID} not found."


def test_realia_keeps_domain_message(realia_repository) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        realia_repository.find_by_realia_id("missing")

    assert str(excinfo.value) == "Realia entry with realiaId 'missing' not found."


def test_bibliography_citation_key_keeps_domain_message(
    bibliography_repository,
) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        bibliography_repository.query_by_citation_key("missing")

    assert str(excinfo.value) == "bibliography citation key missing not found."


def test_bibliography_alias_keeps_domain_message(bibliography_repository) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        bibliography_repository.query_by_alias("missing")

    assert str(excinfo.value) == "bibliography alias missing not found."


def test_file_repository_keeps_domain_message(file_repository) -> None:
    with pytest.raises(NotFoundError) as excinfo:
        file_repository.query_by_file_name("missing.jpg")

    assert str(excinfo.value) == "File missing.jpg not found."
