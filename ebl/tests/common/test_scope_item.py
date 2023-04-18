import pytest
from ebl.common.domain.scopes import ScopeItem, Scope


SCOPE_DATA = [("read", "FOOBAR", "fragments", True), ("write", "BAZ", "", False)]


@pytest.mark.parametrize(
    "prefix,name,suffix,is_open",
    SCOPE_DATA,
)
def test_init(prefix: str, name: str, suffix: str, is_open: bool):
    scope_string = f"{prefix}:{name}-{suffix}".rstrip("-")

    class TestScope(ScopeItem):
        TEST_SCOPE = (scope_string, is_open)

    scope = TestScope.TEST_SCOPE

    assert scope.prefix == prefix
    assert scope.scope_name == name
    assert scope.suffix == suffix
    assert scope.is_open == is_open


@pytest.mark.parametrize(
    "prefix,name,suffix,is_open",
    SCOPE_DATA,
)
def test_from_string(prefix: str, name: str, suffix: str, is_open: bool):
    scope_string = f"{prefix}:{name}-{suffix}".rstrip("-")

    class TestScope(ScopeItem):
        TEST_SCOPE = (scope_string, is_open)

    scope = TestScope.TEST_SCOPE

    assert TestScope.from_string(scope_string) == scope


def test_from_invalid_string():
    scope_string = "invalid scopename"

    class TestScope(ScopeItem):
        pass

    with pytest.raises(
        ValueError,
        match="Invalid scope format: "
        rf"Expected 'action:name\(-collection\)', got {scope_string!r}",
    ):
        TestScope.from_string(scope_string)


@pytest.mark.parametrize(
    "prefix,name,suffix,is_open",
    SCOPE_DATA,
)
def test_str(prefix: str, name: str, suffix: str, is_open: bool):
    scope_string = f"{prefix}:{name}-{suffix}".rstrip("-")

    class TestScope(ScopeItem):
        TEST_SCOPE = (scope_string, is_open)

    scope = TestScope.TEST_SCOPE

    assert TestScope.from_string(str(scope)) == scope


@pytest.mark.parametrize("scope", Scope)
def test_scope_format(scope: Scope):
    scope_string, is_open = scope.value

    assert str(scope) == scope_string
    assert scope.is_open == is_open
