from typing import cast

import pytest

from ebl.tests.fragmentarium.stored_line_shapes import (
    STORAGE_DEFAULTS,
    legacy_shape,
    sparse_shape,
)
from ebl.tests.transliteration.storage_test_helpers import has_key, stored_dump
from ebl.transliteration.application.one_of_line_schema import OneOfLineSchema
from ebl.transliteration.application.token_schemas_signs import (
    ReadingSchema,
    is_legacy_name,
)
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.transliteration.domain.tokens import ValueToken

ATFS = [
    "1. k[u-nu]-uš {d}INANA",
    "1. [ku]-nu {d}utu-ši",
    "1. ku-nu-uš KUR# ⸢ki⸣ %sux gu-du/gu₂",
]
ERASED_ATF = "1. °ku\\ra° ku"


def line_of(atf: str):
    return parse_atf_lark(atf).lines[0]


def api_dump(line) -> dict:
    return cast(dict, OneOfLineSchema().dump(line))


def storage_dump(line) -> dict:
    return stored_dump(OneOfLineSchema(), line)


@pytest.mark.parametrize("atf", ATFS)
def test_storage_dump_omits_default_erasure_and_empty_name_breaks(atf):
    line = line_of(atf)
    stored_line = storage_dump(line)

    assert stored_line == sparse_shape(api_dump(line), STORAGE_DEFAULTS)
    assert not has_key(stored_line, "erasure")
    assert has_key(stored_line, "enclosureType")


def test_storage_dump_keeps_real_name_breaks():
    stored_line = storage_dump(line_of(ATFS[0]))
    reading = stored_line["content"][0]["parts"][0]

    assert [part["value"] for part in reading["nameBreaks"]] == ["["]


def test_storage_dump_keeps_erasure_that_is_not_none():
    erasures = {
        token.get("erasure") for token in storage_dump(line_of(ERASED_ATF))["content"]
    }

    assert erasures >= {"ERASED", "OVER_ERASED"}


@pytest.mark.parametrize("atf", [*ATFS, ERASED_ATF])
def test_api_dump_is_not_sparse(atf):
    api_line = api_dump(line_of(atf))

    assert has_key(api_line, "erasure")
    assert has_key(api_line, "nameBreaks")


@pytest.mark.parametrize("atf", [*ATFS, ERASED_ATF])
@pytest.mark.parametrize(
    "shape",
    [
        lambda line: api_dump(line),
        lambda line: storage_dump(line),
        lambda line: legacy_shape(api_dump(line)),
        lambda line: legacy_shape(storage_dump(line)),
    ],
    ids=["full", "sparse", "legacy", "legacy-sparse"],
)
def test_every_stored_shape_loads_to_the_same_line(atf, shape):
    line = line_of(atf)

    assert OneOfLineSchema().load(shape(line)) == line


BREAK = {"type": "BrokenAway", "value": "["}
PART = {"type": "ValueToken", "value": "k"}


@pytest.mark.parametrize(
    "data,expected",
    [
        ({"nameParts": [PART, BREAK, PART]}, True),
        ({"nameParts": [PART, BREAK, PART], "nameBreaks": [BREAK]}, False),
        ({"nameParts": [PART]}, False),
        ({"nameParts": [PART], "nameBreaks": []}, False),
        ({"nameParts": "ku"}, False),
        ({}, False),
        ("ku", False),
    ],
)
def test_is_legacy_name(data, expected):
    assert is_legacy_name(data) is expected


MULTI_PART_READING = Reading.of((ValueToken.of("k"), ValueToken.of("u")))


def test_storage_dump_keeps_empty_name_breaks_of_a_multi_part_name():
    stored = stored_dump(ReadingSchema(), MULTI_PART_READING)

    assert stored["nameBreaks"] == []
    assert len(stored["nameParts"]) == 2
    assert "erasure" not in stored


def test_storage_dump_omits_empty_name_breaks_of_a_single_part_name():
    stored = stored_dump(ReadingSchema(), Reading.of((ValueToken.of("ku"),)))

    assert "nameBreaks" not in stored
    assert "erasure" not in stored


def test_a_stored_multi_part_name_is_not_read_as_legacy():
    stored = stored_dump(ReadingSchema(), MULTI_PART_READING)

    assert is_legacy_name(stored) is False
    assert ReadingSchema().load(stored) == MULTI_PART_READING
