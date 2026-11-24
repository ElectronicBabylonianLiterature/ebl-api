import json
from typing import Callable, Dict, Sequence, Tuple

import falcon
import pytest
from falcon import testing

from ebl.corpus.domain.chapter import Chapter
from ebl.tests.corpus.chapter_edit_support import ChapterEditRequest, post_edit
from ebl.tests.corpus.lines_edit_support import read_json
from ebl.tests.corpus.word_instances_requests import (
    INSTANCES_QUERY,
    INSTANCES_SUFFIX,
)
from ebl.tests.corpus.word_instances_support import NEW_LEMMA, WORD

MalformedBody = Tuple[object, Sequence[str]]
VALID_BODY: Dict[str, object] = {"word": WORD, "uniqueLemma": list(NEW_LEMMA)}
WORD_FIELD: Sequence[str] = ("word",)
LEMMA_FIELD: Sequence[str] = ("uniqueLemma",)
MALFORMED_BODIES: Sequence[MalformedBody] = (
    ({}, ["uniqueLemma", "word"]),
    ({"word": WORD}, LEMMA_FIELD),
    ({"uniqueLemma": list(NEW_LEMMA)}, WORD_FIELD),
    ({**VALID_BODY, "word": ""}, WORD_FIELD),
    ({**VALID_BODY, "word": None}, WORD_FIELD),
    ({**VALID_BODY, "word": 1}, WORD_FIELD),
    ({**VALID_BODY, "word": True}, WORD_FIELD),
    ({**VALID_BODY, "word": [WORD]}, WORD_FIELD),
    ({**VALID_BODY, "word": {"value": WORD}}, WORD_FIELD),
    ({**VALID_BODY, "uniqueLemma": []}, LEMMA_FIELD),
    ({**VALID_BODY, "uniqueLemma": None}, LEMMA_FIELD),
    ({**VALID_BODY, "uniqueLemma": "ana I"}, LEMMA_FIELD),
    ({**VALID_BODY, "uniqueLemma": {"0": "ana I"}}, LEMMA_FIELD),
    ({**VALID_BODY, "uniqueLemma": [1]}, LEMMA_FIELD),
    ({**VALID_BODY, "uniqueLemma": [None]}, LEMMA_FIELD),
    ({**VALID_BODY, "uniqueLemma": [""]}, LEMMA_FIELD),
    ({**VALID_BODY, "uniqueLemma": ["ana I", ""]}, LEMMA_FIELD),
    ({**VALID_BODY, "uniqueLemma": [["ana I"]]}, LEMMA_FIELD),
    ({**VALID_BODY, "unique_lemma": list(NEW_LEMMA)}, ["unique_lemma"]),
    ({**VALID_BODY, "lemma": list(NEW_LEMMA)}, ["lemma"]),
    ({**VALID_BODY, "revision": "legacy"}, ["revision"]),
    (
        {"word": "", "uniqueLemma": [], "view": "outline"},
        ["uniqueLemma", "view", "word"],
    ),
    ([], ["_schema"]),
    ([VALID_BODY], ["_schema"]),
    (None, ["_schema"]),
    (WORD, ["_schema"]),
)


@pytest.mark.parametrize("malformed", MALFORMED_BODIES)
def test_saving_with_a_malformed_body(
    client: testing.TestClient,
    instances_chapter: Chapter,
    assert_instances_unchanged: Callable[[], None],
    malformed: MalformedBody,
) -> None:
    body, invalid_fields = malformed
    request = ChapterEditRequest(INSTANCES_SUFFIX, json.dumps(body))

    result = post_edit(client, instances_chapter, request, INSTANCES_QUERY)
    result_without_parameters = post_edit(client, instances_chapter, request, "")

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert read_json(result)["title"] == "Request data failed validation"
    assert sorted(read_json(result)["description"]) == list(invalid_fields)
    assert result_without_parameters.json == result.json
    assert_instances_unchanged()


@pytest.mark.parametrize("body", ["", "{", '{"word": "ana", "uniqueLemma": ["ana I"]'])
def test_saving_with_invalid_json(
    client: testing.TestClient,
    instances_chapter: Chapter,
    assert_instances_unchanged: Callable[[], None],
    body: str,
) -> None:
    request = ChapterEditRequest(INSTANCES_SUFFIX, body)

    result = post_edit(client, instances_chapter, request, INSTANCES_QUERY)

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert_instances_unchanged()


def test_malformed_body_is_reported_before_an_unknown_chapter(
    client: testing.TestClient,
) -> None:
    url = "/texts/L/1/1/chapters/invalid/any/lemmatization/instances"

    result = client.simulate_post(url, body=json.dumps({}))
    valid_result = client.simulate_post(url, body=json.dumps(VALID_BODY))

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert valid_result.status == falcon.HTTP_NOT_FOUND
