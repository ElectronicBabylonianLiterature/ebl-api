from typing import Any, Dict, List, Mapping

import pytest

from ebl.io.sparse_tokens.documents import (
    STORED_SIZE,
    TokenFields,
    canonical,
    loadable,
    rewrite_document,
)
from ebl.io.sparse_tokens.token_keys import (
    DERIVED_TOKEN_KEYS,
    OMITTABLE_TOKEN_KEYS,
    STORED_TOKEN_DEFAULTS,
    dropped_token_keys,
    is_token,
    needs_sparse_rewrite,
    token_key_counts,
)

TOKEN = {"type": "Reading", "value": "ku", "flags": [], "extra": 1}


def lossy_spec() -> TokenFields:
    def load(document: Mapping[str, Any]) -> object:
        return document["text"]

    def dump(text: object) -> Dict[str, Any]:
        return {"text": "changed"}

    return TokenFields("fragments", ("text",), load, dump, False)


def test_omittable_token_keys_are_the_marked_fields() -> None:
    assert {
        "erasure",
        "nameBreaks",
        "enclosureType",
        "flags",
        "modifiers",
        "sign",
        "surrogate",
        "alignment",
        "variant",
        "hasVariantAlignment",
        "hasOmittedAlignment",
        "namedEntities",
        "realia",
        "lemmatizable",
        "alignable",
    } == OMITTABLE_TOKEN_KEYS


@pytest.mark.parametrize(
    "value,expected",
    [(TOKEN, True), ({"type": "TextLine"}, False), ({"type": {}}, False), ([], False)],
)
def test_is_token(value: Any, expected: bool) -> None:
    assert is_token(value) is expected


def test_token_key_counts_count_only_token_keys() -> None:
    document = {"lines": [{"type": "TextLine", "content": [TOKEN, TOKEN]}]}

    assert token_key_counts(document) == {"type": 2, "value": 2, "flags": 2, "extra": 2}


def test_dropped_token_keys_ignore_omittable_keys() -> None:
    rewritten = {"type": "Reading", "value": "ku"}

    assert dropped_token_keys([TOKEN], [rewritten]) == {"extra"}


def test_canonical_sorts_enclosure_types_only() -> None:
    value = {"enclosureType": ["B", "A"], "parts": [{"flags": ["?", "!"]}]}

    assert canonical(value) == {
        "enclosureType": ["A", "B"],
        "parts": [{"flags": ["?", "!"]}],
    }


def test_loadable_drops_the_id_and_the_size() -> None:
    assert loadable({"_id": 1, STORED_SIZE: 2, "text": 3}) == {"text": 3}


def test_a_rewrite_that_does_not_reload_equal_is_not_lossless() -> None:
    rewrite = rewrite_document(lossy_spec(), {"_id": 1, "text": [TOKEN]})

    assert rewrite is not None
    assert rewrite.lossless is False
    assert rewrite.fields == {"text": "changed"}


def test_a_document_missing_a_field_is_not_rewritten() -> None:
    assert rewrite_document(lossy_spec(), {"_id": 1}) is None


PART = {"type": "ValueToken", "value": "k"}
BREAK = {"type": "BrokenAway", "value": "["}
SPARSE_READING = {"type": "Reading", "value": "ku", "nameParts": [PART]}


def test_the_stored_defaults_and_derived_keys_come_from_the_schemas() -> None:
    assert DERIVED_TOKEN_KEYS == {"lemmatizable", "alignable"}
    assert STORED_TOKEN_DEFAULTS["erasure"] == ["NONE"]
    assert STORED_TOKEN_DEFAULTS["sign"] == [None]
    assert set(STORED_TOKEN_DEFAULTS) == OMITTABLE_TOKEN_KEYS - DERIVED_TOKEN_KEYS


@pytest.mark.parametrize(
    "token,expected",
    [
        (SPARSE_READING, False),
        ({**SPARSE_READING, "flags": ["#"]}, False),
        ({**SPARSE_READING, "flags": []}, True),
        ({**SPARSE_READING, "lemmatizable": True}, True),
        ({**SPARSE_READING, "nameParts": [PART, BREAK, PART]}, True),
        ({**SPARSE_READING, "nameParts": [PART, PART], "nameBreaks": []}, True),
        ({**SPARSE_READING, "nameParts": [PART, PART], "nameBreaks": [BREAK]}, False),
        ({"type": "TextLine", "flags": []}, False),
    ],
)
def test_needs_sparse_rewrite(token: Dict[str, Any], expected: bool) -> None:
    assert needs_sparse_rewrite({"lines": [{"content": [token]}]}) is expected


def test_a_sparse_document_is_not_loaded() -> None:
    loaded: List[Mapping[str, Any]] = []
    spec = TokenFields("fragments", ("text",), loaded.append, lambda value: {}, False)

    assert rewrite_document(spec, {"_id": 1, "text": [SPARSE_READING]}) is None
    assert loaded == []
