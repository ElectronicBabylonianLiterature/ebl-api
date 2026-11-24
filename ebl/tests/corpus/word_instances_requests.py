import json
from typing import Any, Dict, Sequence

from falcon import testing

from ebl.corpus.domain.chapter import Chapter
from ebl.corpus.domain.chapter_revision import LEGACY_REVISION
from ebl.lemmatization.domain.lemmatization import Lemma
from ebl.tests.corpus.chapter_edit_support import ChapterEditRequest, post_edit
from ebl.tests.corpus.support import create_chapter_url
from ebl.tests.corpus.word_instances_support import NEW_LEMMA, WORD

INSTANCES_SUFFIX = "/lemmatization/instances"
INSTANCES_QUERY = "view=outline&revision=legacy"


def create_count(
    word: str,
    words: int,
    lemmatized: int,
    lines: Sequence[int],
    revision: str = LEGACY_REVISION,
) -> Dict[str, Any]:
    return {
        "word": word,
        "words": words,
        "lemmatized": lemmatized,
        "lines": list(lines),
        "revision": revision,
    }


def create_word_lemma_request(word: object, unique_lemma: object) -> ChapterEditRequest:
    return ChapterEditRequest(
        INSTANCES_SUFFIX, json.dumps({"word": word, "uniqueLemma": unique_lemma})
    )


def post_word_lemma(
    client: testing.TestClient,
    chapter: Chapter,
    query_string: str = INSTANCES_QUERY,
    word: str = WORD,
    lemma: Lemma = NEW_LEMMA,
) -> testing.Result:
    return post_edit(
        client, chapter, create_word_lemma_request(word, list(lemma)), query_string
    )


def get_instances(
    client: testing.TestClient, chapter: Chapter, parameters: Dict[str, Any]
) -> testing.Result:
    result = client.simulate_get(
        create_chapter_url(chapter, INSTANCES_SUFFIX), params=parameters
    )
    assert isinstance(result, testing.Result)
    return result
