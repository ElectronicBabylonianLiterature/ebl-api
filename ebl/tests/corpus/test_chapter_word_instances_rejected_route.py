from typing import Callable, List, Sequence, Tuple

import attr
import falcon
import pytest
from falcon import testing
from pymongo.database import Database

from ebl.corpus.application.word_instances_updater import (
    NO_LEMMA_CHANGE,
    NO_WORD_INSTANCE,
)
from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import (
    LEGACY_REVISION,
    chapter_revision_conflict,
)
from ebl.corpus.infrastructure.mongo_text_repository import MongoTextRepository
from ebl.lemmatization.domain.lemmatization import Lemma
from ebl.tests.corpus.line_move_support import LEMMA, OTHER_LEMMA
from ebl.tests.corpus.lines_edit_support import (
    STALE_REVISION,
    count_chapter_changelog_entries,
    find_stored_chapter,
    read_json,
)
from ebl.tests.corpus.revision_save_support import REFUSED_QUERIES
from ebl.tests.corpus.word_instances_requests import INSTANCES_QUERY, post_word_lemma
from ebl.tests.corpus.word_instances_support import (
    NEW_LEMMA,
    WORD,
    WORDS_WITHOUT_INSTANCE,
)

VIEW_PREFIXES = ("view=outline&", "")
EmptyChange = Tuple[str, Lemma, str]
UNCHANGED_LEMMAS: Sequence[Tuple[str, Lemma]] = (
    ("ku", LEMMA),
    ("buāru", LEMMA),
    ("nu", OTHER_LEMMA),
)
WORDS_WITHOUT_INSTANCE_CHANGES: List[EmptyChange] = [
    (word, NEW_LEMMA, NO_WORD_INSTANCE.format(word)) for word in WORDS_WITHOUT_INSTANCE
]
UNCHANGED_LEMMA_CHANGES: List[EmptyChange] = [
    (word, lemma, NO_LEMMA_CHANGE.format(word, lemma[0]))
    for word, lemma in UNCHANGED_LEMMAS
]
EMPTY_CHANGES: Sequence[EmptyChange] = (
    WORDS_WITHOUT_INSTANCE_CHANGES + UNCHANGED_LEMMA_CHANGES
)


@pytest.mark.parametrize("empty_change", EMPTY_CHANGES, ids=lambda case: case[0])
@pytest.mark.parametrize("view", VIEW_PREFIXES)
def test_change_that_changes_nothing_is_refused(
    client: testing.TestClient,
    instances_chapter: Chapter,
    assert_instances_unchanged: Callable[[], None],
    empty_change: EmptyChange,
    view: str,
) -> None:
    word, lemma, description = empty_change

    result = post_word_lemma(
        client, instances_chapter, f"{view}revision=legacy", word, lemma
    )

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert read_json(result)["description"] == description
    assert_instances_unchanged()


@pytest.mark.parametrize("empty_change", EMPTY_CHANGES, ids=lambda case: case[0])
def test_change_that_changes_nothing_keeps_the_revision(
    client: testing.TestClient,
    text_repository: MongoTextRepository,
    instances_chapter: Chapter,
    empty_change: EmptyChange,
) -> None:
    word, lemma, _ = empty_change

    result = post_word_lemma(client, instances_chapter, word=word, lemma=lemma)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert (
        text_repository.find_chapter_revision(instances_chapter.id_) == LEGACY_REVISION
    )


@pytest.mark.parametrize("refused_query", REFUSED_QUERIES)
def test_save_without_a_valid_revision_and_view_is_refused(
    client: testing.TestClient,
    instances_chapter: Chapter,
    assert_instances_unchanged: Callable[[], None],
    refused_query: Tuple[str, str],
) -> None:
    query_string, description = refused_query

    result = post_word_lemma(client, instances_chapter, query_string)

    assert result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert read_json(result)["description"] == description
    assert_instances_unchanged()


@pytest.mark.parametrize("view", VIEW_PREFIXES)
def test_stale_revision_conflicts_and_the_fresh_revision_succeeds(
    client: testing.TestClient,
    database: Database,
    instances_chapter: Chapter,
    view: str,
) -> None:
    stored_chapter = find_stored_chapter(database, instances_chapter)
    conflict = chapter_revision_conflict(
        instances_chapter.id_, STALE_REVISION, LEGACY_REVISION
    )

    stale_result = post_word_lemma(
        client, instances_chapter, f"{view}revision={STALE_REVISION}"
    )
    chapter_after_conflict = find_stored_chapter(database, instances_chapter)
    changelog_entries_after_conflict = count_chapter_changelog_entries(database)
    fresh_result = post_word_lemma(client, instances_chapter, f"{view}revision=legacy")

    assert stale_result.status == falcon.HTTP_CONFLICT
    assert read_json(stale_result)["description"] == str(conflict)
    assert chapter_after_conflict == stored_chapter
    assert changelog_entries_after_conflict == 0
    assert fresh_result.status == falcon.HTTP_OK
    assert find_stored_chapter(database, instances_chapter) != stored_chapter
    assert count_chapter_changelog_entries(database) == 1


def test_second_save_at_the_same_revision_conflicts(
    client: testing.TestClient, database: Database, instances_chapter: Chapter
) -> None:
    first_result = post_word_lemma(client, instances_chapter)
    stored_chapter = find_stored_chapter(database, instances_chapter)

    second_result = post_word_lemma(client, instances_chapter, lemma=NEW_LEMMA[:1])

    assert first_result.status == falcon.HTTP_OK
    assert second_result.status == falcon.HTTP_CONFLICT
    assert find_stored_chapter(database, instances_chapter) == stored_chapter
    assert count_chapter_changelog_entries(database) == 1


@pytest.mark.parametrize(
    "word,lemma", [(WORDS_WITHOUT_INSTANCE[0], NEW_LEMMA), ("ku", LEMMA)]
)
def test_stale_revision_is_reported_before_a_change_that_changes_nothing(
    client: testing.TestClient,
    instances_chapter: Chapter,
    assert_instances_unchanged: Callable[[], None],
    word: str,
    lemma: Lemma,
) -> None:
    result = post_word_lemma(
        client, instances_chapter, f"revision={STALE_REVISION}", word, lemma
    )

    assert result.status == falcon.HTTP_CONFLICT
    assert_instances_unchanged()


@pytest.mark.parametrize("revision", [LEGACY_REVISION, STALE_REVISION])
def test_saving_in_an_unknown_chapter(
    client: testing.TestClient,
    instances_chapter: Chapter,
    assert_instances_unchanged: Callable[[], None],
    revision: str,
) -> None:
    missing_chapter = attr.evolve(
        instances_chapter, name=f"{instances_chapter.name} missing"
    )

    result = post_word_lemma(
        client, missing_chapter, f"view=outline&revision={revision}"
    )

    assert result.status == falcon.HTTP_NOT_FOUND
    assert_instances_unchanged()


@pytest.mark.parametrize("query_string", ["", INSTANCES_QUERY, "revision=legacy"])
def test_saving_requires_write_scope(
    guest_client: testing.TestClient,
    instances_chapter: Chapter,
    assert_instances_unchanged: Callable[[], None],
    query_string: str,
) -> None:
    result = post_word_lemma(guest_client, instances_chapter, query_string)

    assert result.status == falcon.HTTP_FORBIDDEN
    assert_instances_unchanged()


def test_refused_save_can_be_followed_by_a_save_at_the_same_revision(
    client: testing.TestClient, database: Database, instances_chapter: Chapter
) -> None:
    refused_result = post_word_lemma(client, instances_chapter, word="missing")

    result = post_word_lemma(client, instances_chapter, word=WORD)

    assert refused_result.status == falcon.HTTP_UNPROCESSABLE_ENTITY
    assert read_json(refused_result)["description"] == (
        'The chapter has no instance of the word "missing". Nothing was saved.'
    )
    assert result.status == falcon.HTTP_OK
    assert count_chapter_changelog_entries(database) == 1
