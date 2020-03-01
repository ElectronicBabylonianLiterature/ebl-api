from ebl.transliteration.application.line_schemas import (
    ScopeContainerSchema,
    StateDollarLineSchema,
)
from ebl.transliteration.application.token_schemas import dump_tokens
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import ScopeContainer, StateDollarLine
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
    line = StateDollarLine(
        atf.Qualification.AT_LEAST,
        atf.Extent.BEGINNING_OF,
        ScopeContainer(atf.Surface.OBVERSE),
        atf.State.BLANK,
        atf.DollarStatus.UNCERTAIN,
    )
    expected = {
        "prefix": "$",
        "content": dump_tokens([ValueToken(" at least beginning of obverse blank ?")]),
        "type": "StateDollarLine",
        "qualification": "AT_LEAST",
        "extent": "BEGINNING_OF",
        "scope": {"type": "Surface", "content": "OBVERSE", "text": ""},
        "state": "BLANK",
        "status": "UNCERTAIN",
    }

    assert StateDollarLineSchema().dump(line) == expected
    assert StateDollarLineSchema().load(expected) == line
