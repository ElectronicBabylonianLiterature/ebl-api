from typing import Any, Dict, Iterator, List, cast

import pytest

from ebl.transliteration.application.token_schemas import OneOfTokenSchema
from ebl.transliteration.application.token_schemas_signs import NamedSignSchema
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_line
from ebl.transliteration.domain.sign_token_base import NamedSign
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Token

BROKEN_AWAY_SHAPES = [
    "1. ku",
    "1. k]u",
    "1. [ku]",
    "1. [ku",
    "1. ku]",
    "1. k[u]r",
    "1. [k]u[r]",
    "1. bu[l]u[g]",
    "1. KU]R",
    "1. [KU]",
    "1. 1]0",
    "1. [1]0",
    "1. ku[r]-ra",
    "1. {d}[e]n",
    "1. [...]-ku",
    "1. {d}utu-ši",
]


def _walk(token: Token) -> Iterator[Token]:
    yield token
    for part in token.parts:
        yield from _walk(part)


def _named_signs(atf: str) -> List[NamedSign]:
    line = cast(TextLine, parse_line(atf))
    return [
        token
        for content in line.content
        for token in _walk(content)
        if isinstance(token, NamedSign)
    ]


@pytest.mark.parametrize("atf", BROKEN_AWAY_SHAPES)
def test_a_name_takes_exactly_one_fewer_break_than_it_has_parts(atf: str) -> None:
    signs = _named_signs(atf)

    counts = [(len(sign.name_parts), len(sign.name_breaks)) for sign in signs]

    assert counts != []
    assert all(breaks == parts - 1 for parts, breaks in counts)


@pytest.mark.parametrize("atf", BROKEN_AWAY_SHAPES)
def test_the_written_order_splits_back_by_position(atf: str) -> None:
    signs = _named_signs(atf)

    written = [tuple(sign.name_tokens) for sign in signs]

    assert [tokens[0::2] for tokens in written] == [
        tuple(sign.name_parts) for sign in signs
    ]
    assert [tokens[1::2] for tokens in written] == [
        tuple(sign.name_breaks) for sign in signs
    ]


def _dump(schema: NamedSignSchema, sign: NamedSign) -> Dict[str, Any]:
    return cast(Dict[str, Any], schema.dump(sign))


def _as_legacy_payload(sign: NamedSign, dumped: Dict[str, Any]) -> Dict[str, Any]:
    legacy = {key: value for key, value in dumped.items() if key != "nameBreaks"}
    legacy["nameParts"] = OneOfTokenSchema().dump(list(sign.name_tokens), many=True)
    return legacy


@pytest.mark.parametrize("atf", BROKEN_AWAY_SHAPES)
def test_a_legacy_payload_separates_back_into_the_same_arrays(atf: str) -> None:
    schema = NamedSignSchema()
    for sign in _named_signs(atf):
        dumped = _dump(schema, sign)
        legacy = _as_legacy_payload(sign, dumped)

        separated = schema.separate_legacy_name_parts(legacy)

        assert separated["nameParts"] == dumped["nameParts"]
        assert separated["nameBreaks"] == dumped["nameBreaks"]
