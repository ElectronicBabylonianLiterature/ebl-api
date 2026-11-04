import json

import pytest

from ebl.fragmentarium.application.fragment_query_preview import preview_line_of
from ebl.tests.fragmentarium.fragment_query_preview_test_helpers import dumped
from ebl.tests.fragmentarium.stored_line_shapes import (
    interleaved,
    legacy_shape,
    sparse_shape,
)
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark

BROKEN_NAME_ATF = "1. k[u-nu]-uš {d}INANA"


@pytest.fixture
def full_line() -> dict:
    return dumped(parse_atf_lark(BROKEN_NAME_ATF).lines[0])


def test_sparse_fixture_omits_the_default_fields(full_line):
    serialized = json.dumps(sparse_shape(full_line))

    assert '"erasure"' not in serialized
    assert '"enclosureType": []' not in serialized
    assert "BROKEN_AWAY" in serialized


def test_legacy_fixture_interleaves_name_breaks(full_line):
    legacy_line = legacy_shape(full_line)
    reading = legacy_line["content"][0]["parts"][0]

    assert "nameBreaks" not in json.dumps(legacy_line)
    assert [part["type"] for part in reading["nameParts"]] == [
        "ValueToken",
        "BrokenAway",
        "ValueToken",
    ]


def test_interleaved_keeps_parts_after_the_last_break():
    assert interleaved(["k", "u", "x"], ["["]) == ["k", "[", "u", "x"]


@pytest.mark.parametrize("shape", [sparse_shape, legacy_shape])
def test_preview_of_a_stored_shape_is_the_full_api_shape(full_line, shape):
    stored_line = shape(full_line)

    assert stored_line != full_line
    assert preview_line_of(4, stored_line) == {**full_line, "index": 4}


def test_preview_of_a_sparse_legacy_line_is_the_full_api_shape(full_line):
    stored_line = sparse_shape(legacy_shape(full_line))

    assert preview_line_of(0, stored_line) == {**full_line, "index": 0}


def test_preview_drops_fields_the_line_schema_does_not_know(full_line):
    preview = preview_line_of(0, {**full_line, "storedOnly": True})

    assert preview == {**full_line, "index": 0}
