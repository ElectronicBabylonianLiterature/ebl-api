from typing import Dict, Mapping, Sequence, cast

import pytest
from marshmallow import ValidationError

from ebl.sumerian_dictionary.domain.sumerian_word import (
    AttingerHeadword,
    AttingerSource,
    HeadwordMark,
    SumerianWord,
)
from ebl.sumerian_dictionary.infrastructure.sumerian_word_schemas import (
    SumerianWordDocumentSchema,
    SumerianWordSchema,
)
from ebl.tests.sumerian_dictionary.test_sumerian_word_schemas import MINIMAL_DOCUMENT


def _document(marks: Sequence[object]) -> Mapping[str, object]:
    headword = {"text": "lugal", "display": "lugal", "marks": marks}
    attinger = {
        "entryId": "att-1",
        "node": "n",
        "letter": "L",
        "depth": 1,
        "partOfSpeech": "N",
        "headword": headword,
    }
    return {**MINIMAL_DOCUMENT, "sources": {"attinger": attinger}}


def test_marks_load_as_objects() -> None:
    marks = [
        {"start": 0, "end": 1, "style": "b"},
        {"start": 3, "end": 5, "style": "sub"},
    ]

    word = cast(SumerianWord, SumerianWordDocumentSchema().load(_document(marks)))
    dumped = cast(Dict[str, dict], SumerianWordSchema().dump(word))

    assert word.sources.attinger == AttingerSource(
        "att-1",
        "n",
        "L",
        1,
        "N",
        AttingerHeadword(
            "lugal", "lugal", (HeadwordMark(0, 1, "b"), HeadwordMark(3, 5, "sub"))
        ),
    )
    assert dumped["sources"]["attinger"]["headword"]["marks"] == marks


@pytest.mark.parametrize(
    "mark",
    [[0, 1, "b"], {"start": 0, "end": 1}, {"start": "a", "end": 1, "style": "b"}],
)
def test_marks_that_are_not_complete_objects_are_rejected(mark: object) -> None:
    with pytest.raises(ValidationError):
        SumerianWordDocumentSchema().load(_document([mark]))
