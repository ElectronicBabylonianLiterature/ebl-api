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


def test_strict_dollar_line_schema():
    line = StrictDollarLine(
        atf.Qualification.AT_LEAST,
        atf.Extent.BEGINNING_OF,
        ScopeContainer(atf.Surface.OBVERSE),
        atf.State.BLANK,
        atf.Status.UNCERTAIN,
    )
    expected = {
        "prefix": "$",
        "content": dump_tokens([ValueToken("at least beginning of obverse blank ?")]),
        "type": "StrictDollarLine",
        "qualification": "AT_LEAST",
        "extent": {"type": "Extent", "value": "BEGINNING_OF"},
        "scope": {"type": "Surface", "content": "OBVERSE", "text": ""},
        "state": "BLANK",
        "status": "UNCERTAIN",
    }

    assert StrictDollarLineSchema().dump(line) == expected
    assert StrictDollarLineSchema().load(expected) == line
