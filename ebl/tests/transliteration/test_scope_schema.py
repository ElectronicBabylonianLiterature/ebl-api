from ebl.transliteration.application.dollar_line_schemas import ScopeContainerSchema
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.dollar_line import ScopeContainer


def test_dump_scope_schema():
    scope = ScopeContainer(atf.Surface.OBVERSE, "")
    dump = ScopeContainerSchema().dump(scope)
    assert dump == {"type": "Surface", "content": "OBVERSE", "text": ""}


def test_load_scope_schema():
    load_dict = {"type": "Surface", "content": "OBVERSE", "text": ""}
    scope = ScopeContainerSchema().load(load_dict)
    assert ScopeContainer(atf.Surface.OBVERSE, "") == scope
