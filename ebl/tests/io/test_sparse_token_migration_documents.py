from typing import Any, Dict, List, Mapping, cast

import pytest

from ebl.io.sparse_tokens.documents import (
    STORED_SIZE,
    MissingFields,
    TokenFields,
    canonical,
    fragment_token_fields,
    loadable,
    rewrite_document,
)
from ebl.io.sparse_tokens.token_keys import (
    DERIVED_TOKEN_KEYS,
    OMITTABLE_TOKEN_KEYS,
    STORED_TOKEN_DEFAULTS,
    dropped_keys,
    is_token,
    key_counts,
    needs_sparse_rewrite,
)
from ebl.transliteration.application.text_schema import TextSchema
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark

TOKEN = {"type": "Reading", "value": "ku", "flags": [], "extra": 1}


def lossy_token_fields() -> TokenFields:
    def load(document: Mapping[str, Any]) -> object:
        return document["text"]

    def dump(text: object) -> Dict[str, Any]:
        return {"text": "changed"}

    return TokenFields("fragments", ("text",), load, dump, False, True)


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


def test_key_counts_count_every_key() -> None:
    document = {"lines": [{"type": "TextLine", "content": [TOKEN, TOKEN]}]}

    assert key_counts(document) == {
        (None, "lines"): 1,
        (None, "type"): 1,
        (None, "content"): 1,
        ("Reading", "type"): 2,
        ("Reading", "value"): 2,
        ("Reading", "flags"): 2,
        ("Reading", "extra"): 2,
    }


def test_dropped_keys_ignore_keys_omittable_for_the_token_type() -> None:
    rewritten = {"type": "Reading", "value": "ku"}

    assert dropped_keys([TOKEN], [rewritten]) == {"extra"}


def test_dropped_keys_report_line_keys() -> None:
    line = {"type": "TextLine", "content": [], "lineKey": 1}

    assert dropped_keys([line], [{"type": "TextLine", "content": []}]) == {"lineKey"}


def test_a_key_omittable_only_for_another_token_type_is_reported() -> None:
    word = {"type": "Word", "value": "ku", "flags": ["#"]}

    assert dropped_keys([word], [{"type": "Word", "value": "ku"}]) == {"flags"}


def test_a_key_kept_on_a_token_does_not_excuse_its_drop_elsewhere() -> None:
    reading = {"type": "Reading", "value": "ku", "flags": ["#"]}
    original = [reading, {"start": {"number": 1, "flags": ["#"]}}]
    rewritten = [reading, {"start": {"number": 1}}]

    assert dropped_keys(original, rewritten) == {"flags"}


def test_a_line_number_key_dropped_next_to_a_flagged_token_is_reported() -> None:
    text = cast(dict, TextSchema().dump(parse_atf_lark("1-2. ku#")))
    text["lines"][0]["lineNumber"]["start"]["flags"] = ["#"]
    document = {"_id": "X.9", "text": text, STORED_SIZE: 1000}

    rewrite = rewrite_document(fragment_token_fields(), document, full_check=True)

    assert rewrite is not None
    assert rewrite.dropped_keys == {"flags"}


def test_canonical_sorts_enclosure_types_only() -> None:
    value = {"enclosureType": ["B", "A"], "parts": [{"flags": ["?", "!"]}]}

    assert canonical(value) == {
        "enclosureType": ["A", "B"],
        "parts": [{"flags": ["?", "!"]}],
    }


def test_loadable_drops_the_id_and_the_size() -> None:
    assert loadable({"_id": 1, STORED_SIZE: 2, "text": 3}) == {"text": 3}


def test_a_rewrite_that_does_not_reload_equal_is_not_lossless() -> None:
    rewrite = rewrite_document(lossy_token_fields(), {"_id": 1, "text": [TOKEN]})

    assert rewrite is not None
    assert rewrite.lossless is False
    assert rewrite.fields == {"text": "changed"}


def test_a_document_missing_an_optional_field_is_not_rewritten() -> None:
    assert rewrite_document(lossy_token_fields(), {"_id": 1}) is None


def test_a_document_missing_a_required_field_is_unreadable() -> None:
    token_fields = TokenFields(
        "chapters", ("lines", "manuscripts"), dict, lambda value: {}, True, False
    )

    with pytest.raises(MissingFields, match="missing manuscripts"):
        rewrite_document(token_fields, {"_id": 1, "lines": []})


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
        ({**SPARSE_READING, "nameParts": [PART, PART], "nameBreaks": []}, False),
        ({**SPARSE_READING, "nameParts": [PART, PART]}, True),
        ({**SPARSE_READING, "nameBreaks": []}, True),
        ({**SPARSE_READING, "nameParts": [PART, PART], "nameBreaks": [BREAK]}, False),
        ({"type": "TextLine", "flags": []}, False),
    ],
)
def test_needs_sparse_rewrite(token: Dict[str, Any], expected: bool) -> None:
    assert needs_sparse_rewrite({"lines": [{"content": [token]}]}) is expected


def test_a_sparse_document_is_not_loaded() -> None:
    loaded: List[Mapping[str, Any]] = []
    token_fields = TokenFields(
        "fragments", ("text",), loaded.append, lambda value: {}, False, True
    )

    assert rewrite_document(token_fields, {"_id": 1, "text": [SPARSE_READING]}) is None
    assert loaded == []
