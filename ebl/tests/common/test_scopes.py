import pytest

from ebl.common.domain.scopes import Scope


def test_from_string_round_trip() -> None:
    assert Scope.from_string("read:bibliography") is Scope.READ_BIBLIOGRAPHY


def test_from_string_with_suffix() -> None:
    assert Scope.from_string("read:ARG-folios") is Scope.READ_ARG_FOLIOS


def test_from_string_unknown_scope_raises() -> None:
    with pytest.raises(ValueError, match="Unknown scope: read:nonexistent"):
        Scope.from_string("read:nonexistent")


def test_from_string_malformed_raises() -> None:
    with pytest.raises(ValueError, match="Unexepcted scope format"):
        Scope.from_string("noformat")


def test_is_restricted() -> None:
    assert Scope.WRITE_TEXTS.is_restricted is True
    assert Scope.READ_BIBLIOGRAPHY.is_restricted is False


def test_str_round_trip() -> None:
    assert str(Scope.READ_BIBLIOGRAPHY) == "read:bibliography"
    assert str(Scope.READ_ARG_FOLIOS) == "read:ARG-folios"
