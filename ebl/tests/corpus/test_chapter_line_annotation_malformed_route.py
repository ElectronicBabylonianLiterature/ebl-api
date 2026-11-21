import json
from typing import Callable, Dict, Sequence, Tuple

import falcon
import pytest
from falcon import testing

from ebl.corpus.domain.chapter import Chapter
from ebl.tests.corpus.chapter_edit_support import ChapterEditRequest, post_edit
from ebl.tests.corpus.line_annotation_kind import ANNOTATION_QUERY, AnnotationKind
from ebl.tests.corpus.line_annotation_kinds import ALIGNMENT, LEMMATIZATION
from ebl.tests.corpus.lines_edit_support import read_json

MalformedBody = Tuple[AnnotationKind, object, Sequence[str]]
VALID_TOKEN: Dict[str, object] = {"value": "ku"}
VARIANT: Dict[str, object] = {
    "value": "ku",
    "alignment": 1,
    "variant": "KU",
    "type": "Word",
    "language": "SUMERIAN",
}


def create_alignment_body(token: object) -> Dict[str, object]:
    return {"alignment": [[{"alignment": [token], "omittedWords": []}]]}


def create_lemmatization_body(token: object) -> Dict[str, object]:
    return {"lemmatization": [{"reconstruction": [token], "manuscripts": [[token]]}]}


MALFORMED_ALIGNMENTS: Sequence[Tuple[object, Sequence[str]]] = (
    ({}, ["alignment"]),
    ({"alignment": None}, ["alignment"]),
    ({"alignment": "ku"}, ["alignment"]),
    ({"alignment": {"0": []}}, ["alignment"]),
    ({"alignment": [{"alignment": [], "omittedWords": []}]}, ["alignment"]),
    ({"alignment": [[[{"alignment": [], "omittedWords": []}]]]}, ["alignment"]),
    ({"alignment": [[{"alignment": []}]]}, ["alignment"]),
    ({"alignment": [[{"omittedWords": []}]]}, ["alignment"]),
    ({"alignment": [[{"alignment": [], "omittedWords": ["a"]}]]}, ["alignment"]),
    ({"alignment": [[{"alignment": [], "omittedWords": [], "id": 1}]]}, ["alignment"]),
    ({"alignment": [], "lines": []}, ["lines"]),
    ({"lemmatization": []}, ["alignment", "lemmatization"]),
    (create_alignment_body({}), ["alignment"]),
    (create_alignment_body("ku"), ["alignment"]),
    (create_alignment_body({"value": 1}), ["alignment"]),
    (create_alignment_body({"value": "ku", "alignment": "one"}), ["alignment"]),
    (create_alignment_body({"value": "ku", "uniqueLemma": []}), ["alignment"]),
    (create_alignment_body({**VARIANT, "type": "Unknown"}), ["alignment"]),
    (create_alignment_body({**VARIANT, "type": ""}), ["alignment"]),
    (create_alignment_body({**VARIANT, "type": 1}), ["alignment"]),
    (create_alignment_body({**VARIANT, "language": "NOPE"}), ["alignment"]),
    (create_alignment_body({**VARIANT, "language": ""}), ["alignment"]),
    (create_alignment_body({**VARIANT, "variant": "ku-["}), ["alignment"]),
    ([], ["_schema"]),
    (None, ["_schema"]),
    ("alignment", ["_schema"]),
)
MALFORMED_LEMMATIZATIONS: Sequence[Tuple[object, Sequence[str]]] = (
    ({}, ["lemmatization"]),
    ({"lemmatization": None}, ["lemmatization"]),
    ({"lemmatization": "ku"}, ["lemmatization"]),
    ({"lemmatization": [[]]}, ["lemmatization"]),
    ({"lemmatization": [{}]}, ["lemmatization"]),
    ({"lemmatization": [{"reconstruction": []}]}, ["lemmatization"]),
    ({"lemmatization": [{"manuscripts": []}]}, ["lemmatization"]),
    (
        {"lemmatization": [{"reconstruction": [], "manuscripts": [VALID_TOKEN]}]},
        ["lemmatization"],
    ),
    (
        {"lemmatization": [{"reconstruction": [], "manuscripts": [], "id": 1}]},
        ["lemmatization"],
    ),
    ({"lemmatization": [], "lines": []}, ["lines"]),
    ({"alignment": []}, ["alignment", "lemmatization"]),
    (create_lemmatization_body({}), ["lemmatization"]),
    (create_lemmatization_body("ku"), ["lemmatization"]),
    (create_lemmatization_body({"value": 1}), ["lemmatization"]),
    (
        create_lemmatization_body({"value": "ku", "uniqueLemma": "aklu I"}),
        ["lemmatization"],
    ),
    (create_lemmatization_body({"value": "ku", "uniqueLemma": [1]}), ["lemmatization"]),
    (create_lemmatization_body({"value": "ku", "alignment": 1}), ["lemmatization"]),
    ([], ["_schema"]),
    (None, ["_schema"]),
    ("lemmatization", ["_schema"]),
)
MALFORMED_BODIES: Sequence[MalformedBody] = [
    (kind, body, fields)
    for kind, bodies in (
        (ALIGNMENT, MALFORMED_ALIGNMENTS),
        (LEMMATIZATION, MALFORMED_LEMMATIZATIONS),
    )
    for body, fields in bodies
]


@pytest.mark.parametrize("malformed", MALFORMED_BODIES)
def test_saving_with_a_malformed_body(
    client: testing.TestClient,
    annotation_chapter: Chapter,
    assert_nothing_saved: Callable[[], None],
    malformed: MalformedBody,
) -> None:
    kind, body, invalid_fields = malformed
    request = ChapterEditRequest(f"/lines/0/{kind.name}", json.dumps(body))

    result = post_edit(client, annotation_chapter, request, ANNOTATION_QUERY)
    result_without_parameters = post_edit(client, annotation_chapter, request, "")

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert read_json(result)["title"] == "Request data failed validation"
    assert sorted(read_json(result)["description"]) == invalid_fields
    assert result_without_parameters.json == result.json
    assert_nothing_saved()


@pytest.mark.parametrize("body", ["", "{", '{"alignment": [], "lemmatization": []'])
def test_saving_with_invalid_json(
    client: testing.TestClient,
    annotation_chapter: Chapter,
    assert_nothing_saved: Callable[[], None],
    annotation_kind: AnnotationKind,
    body: str,
) -> None:
    request = ChapterEditRequest(f"/lines/0/{annotation_kind.name}", body)

    result = post_edit(client, annotation_chapter, request, ANNOTATION_QUERY)

    assert result.status == falcon.HTTP_BAD_REQUEST
    assert_nothing_saved()
