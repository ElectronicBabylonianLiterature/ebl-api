import pytest

from ebl.transliteration.application.line_schemas import (
    ScopeContainerSchema,
    StrictDollarLineSchema,
)
from ebl.transliteration.application.token_schemas import dump_tokens
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.line import ScopeContainer, StrictDollarLine
from ebl.transliteration.domain.tokens import ValueToken


def test_dump_scope_schema():
    scope = ScopeContainer(atf.Surface.OBVERSE, "")
    dump = ScopeContainerSchema().dump(scope)
    assert dump == {"type": "Surface", "content": "OBVERSE", "text": ""}


def test_load_scope_schema():
    load_dict = {"type": "Surface", "content": "OBVERSE", "text": ""}
    scope = ScopeContainerSchema().load(load_dict)
    assert ScopeContainer(atf.Surface.OBVERSE, "") == scope


def test_dump_scope():
    atf_surface = ScopeContainerSchema.dump_scope("Surface", "OBVERSE")
    assert ScopeContainer(atf.Surface.OBVERSE, "") == ScopeContainer(atf_surface, "")


def test_strict_dollar_line_schema():
    line = StrictDollarLine(
        atf.Qualification("at least"),
        atf.Extent("beginning of"),
        ScopeContainer(atf.Surface.from_atf("obverse")),
        atf.State("blank"),
        atf.Status("?"),
    )
    expected = {
        "prefix": "$",
        "content": dump_tokens([ValueToken("at least beginning of obverse blank ?")]),
        "type": "StrictDollarLine",
        "qualification": "at least",
        "extent": {"type": "Extent", "value": "beginning of"},
        "scope_container": {"type": "Surface", "content": "OBVERSE", "text": ""},
        "state": "blank",
        "status": "?",
    }

    dump = StrictDollarLineSchema().dump(line)
    # assert dump == expected
    assert line == StrictDollarLineSchema().load(expected)


def test_strict_dollar_line_schema():
    line = StrictDollarLine(
        atf.Qualification("at least"),
        2,
        ScopeContainer(atf.Surface.from_atf("obverse")),
        atf.State("blank"),
        atf.Status("?"),
    )
    expected = {
        "prefix": "$",
        "content": dump_tokens([ValueToken("at least 2 obverse blank ?")]),
        "type": "StrictDollarLine",
        "qualification": "at least",
        "extent": {"type": "int", "value": "2"},
        "scope_container": {"type": "Surface", "content": "OBVERSE", "text": ""},
        "state": "blank",
        "status": "?",
    }

    dump = StrictDollarLineSchema().dump(line)
    assert dump == expected
    assert line == StrictDollarLineSchema().load(expected)


def test_strict_dollar_line_schema_fail():
    line = StrictDollarLine(
        None,
        atf.Extent("beginning of"),
        ScopeContainer(atf.Surface.from_atf("obverse")),
        atf.State("blank"),
        atf.Status("?"),
    )
    expected = {
        "prefix": "$",
        "content": dump_tokens([ValueToken("beginning of obverse blank ?")]),
        "type": "StrictDollarLine",
        "qualification": None,
        "extent": {"type": "Extent", "value": "beginning of"},
        "scope_container": {"type": "Surface", "content": "OBVERSE", "text": ""},
        "state": "blank",
        "status": "?",
    }
    dump = StrictDollarLineSchema().dump(line)
    assert dump == expected
    assert line == StrictDollarLineSchema().load(expected)


def test_strict_dollar_line_schema_fail():
    expected = {
        "prefix": "$",
        "content": dump_tokens([ValueToken("some obverse")]),
        "type": "StrictDollarLine",
        "qualification": None,
        "extent": {"type": "Extent", "value": "some"},
        "scope_container": {"type": "Surface", "content": "OBVERSE", "text": ""},
        "state": None,
        "status": None,
    }

    line = StrictDollarLine(
        None, atf.Extent.SOME, ScopeContainer(atf.Surface.OBVERSE), None, None
    )

    assert StrictDollarLineSchema().load(expected) == line
    assert StrictDollarLineSchema().dump(line) == expected
