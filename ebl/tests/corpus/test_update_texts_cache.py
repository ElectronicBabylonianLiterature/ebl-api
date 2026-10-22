import runpy
import sys
from contextlib import redirect_stdout
from io import StringIO
from multiprocessing.pool import ThreadPool
from pathlib import Path

import attr
import falcon
import pytest
from falcon import testing
from pymongo.database import Database

import ebl.app
from ebl.context import Context
from ebl.corpus import update_texts
from ebl.corpus.application.corpus import Corpus
from ebl.corpus.domain.chapter import Chapter
from ebl.tests.corpus import test_chapter_cache_races
from ebl.tests.corpus.support import create_chapter_url, simulate_get
from ebl.transliteration.domain.atf import ATF_PARSER_VERSION


cached_chapter = test_chapter_cache_races.cached_chapter


@pytest.fixture
def batch_context(context: Context, monkeypatch: pytest.MonkeyPatch) -> Context:
    monkeypatch.setattr(update_texts, "create_context", lambda: context)
    monkeypatch.setattr(ebl.app, "create_context", lambda: context)
    return context


def test_batch_worker_invalidates_every_chapter_and_line_display(
    batch_context: Context,
    cached_chapter: Chapter,
    client: testing.TestClient,
    database: Database,
) -> None:
    other_chapter = attr.evolve(cached_chapter, name="another chapter", order=1)
    batch_context.text_repository.create_chapter(other_chapter)
    chapters = (cached_chapter, other_chapter)
    endpoints = [
        create_chapter_url(chapter, suffix)
        for chapter in chapters
        for suffix in ("/display", "/lines/0")
    ]
    for endpoint in endpoints:
        assert simulate_get(client, endpoint).status == falcon.HTTP_OK
    assert database["cache"].count_documents({}) == 4

    result = update_texts.update(cached_chapter.text_id)

    assert result == update_texts.State(updated=1)
    assert database["cache"].count_documents({}) == 0
    for chapter in chapters:
        assert batch_context.text_repository.find_chapter(
            chapter.id_
        ).parser_version == (ATF_PARSER_VERSION)
        assert database["chapter_cache_state"].find_one({"_id": str(chapter.id_)}) == {
            "_id": str(chapter.id_),
            "pending": 0,
            "revision": 2,
        }
    for endpoint in endpoints:
        assert simulate_get(client, endpoint).status == falcon.HTTP_OK
    assert database["cache"].count_documents({"chapterCacheRevision": 2}) == 4


def test_failed_batch_finishes_markers_and_reports_the_error(
    batch_context: Context,
    cached_chapter: Chapter,
    monkeypatch: pytest.MonkeyPatch,
    database: Database,
) -> None:
    def reject(*args: object, **kwargs: object) -> None:
        raise ValueError("rejected batch")

    monkeypatch.setattr(Corpus, "find_chapter", reject)
    result = update_texts.update(cached_chapter.text_id)
    error = f"{cached_chapter.text_id.category} {cached_chapter.text_id.index}\trejected batch"
    assert result == update_texts.State(invalid=1, errors=[error])
    merged = result.merge(update_texts.State(updated=2))
    assert merged.to_tsv() == f"{error}\n# Updated: 2\n# Invalid: 1"
    assert database["chapter_cache_state"].find_one(
        {"_id": str(cached_chapter.id_)}
    ) == {
        "_id": str(cached_chapter.id_),
        "pending": 0,
        "revision": 2,
    }


def test_batch_cli_uses_shared_cache_and_writes_its_report(
    batch_context: Context,
    cached_chapter: Chapter,
    monkeypatch: pytest.MonkeyPatch,
    tmp_path: Path,
) -> None:
    script = Path(update_texts.__file__).resolve()
    cache = batch_context.custom_cache
    cache.get_or_create(cached_chapter.id_, str(cached_chapter.id_), lambda: {})
    monkeypatch.setattr("multiprocessing.Pool", ThreadPool)
    monkeypatch.setattr(sys, "argv", [str(script), "--workers", "1"])
    monkeypatch.chdir(tmp_path)

    stdout = StringIO()
    with redirect_stdout(stdout):
        runpy.run_path(str(script), run_name="__main__")

    assert (tmp_path / "invalid_texts.tsv").read_text() == "# Updated: 1\n# Invalid: 0"
    assert "Update texts completed!" in stdout.getvalue()
    assert cache._mongo_cache_repository.chapter_revision(str(cached_chapter.id_)) == 2
