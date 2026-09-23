from typing import Any, Mapping, Optional

import pytest

from ebl.common.domain.scopes import Scope
from ebl.errors import NotFoundError
from ebl.files.application.file_repository import File, FileRepository
from ebl.users.domain.user import ApiUser, Guest


class _StubFile(File):
    def __init__(self, metadata: Mapping[str, Any]) -> None:
        self._metadata = metadata

    @property
    def metadata(self) -> Mapping[str, Any]:
        return self._metadata

    @property
    def length(self) -> int:
        return 0

    @property
    def content_type(self) -> Optional[str]:
        return None

    def read(self, size=-1) -> bytes:
        return b""

    def close(self) -> None:
        return None


class _ScopedUser(ApiUser):
    def __init__(self, granted: Scope) -> None:
        super().__init__("test")
        self._granted = granted

    def has_scope(self, scope: Scope) -> bool:
        return scope == self._granted


class _StubRepository(FileRepository):
    def __init__(self, present: bool) -> None:
        self._present = present

    def query_by_file_name(self, file_name: str) -> File:
        if not self._present:
            raise NotFoundError(file_name)
        return _StubFile({})


ARG_FOLIOS = Scope.READ_ARG_FOLIOS


def test_a_file_is_readable_by_a_user_holding_its_scope() -> None:
    file = _StubFile({"scope": "ARG-folios"})

    assert file.can_be_read_by(_ScopedUser(ARG_FOLIOS)) is True


def test_a_file_is_not_readable_by_a_user_without_its_scope() -> None:
    file = _StubFile({"scope": "ARG-folios"})

    assert file.can_be_read_by(Guest()) is False


def test_an_open_scope_is_readable_by_anyone() -> None:
    file = _StubFile({"scope": "ARGC-folios"})

    assert file.can_be_read_by(Guest()) is True


def test_an_unknown_scope_string_is_rejected() -> None:
    file = _StubFile({"scope": "not-a-real-scope"})

    with pytest.raises(ValueError):
        file.can_be_read_by(Guest())


def test_query_if_file_exists_is_true_when_the_file_is_there() -> None:
    assert _StubRepository(present=True).query_if_file_exists("photo.jpg") is True


def test_query_if_file_exists_is_false_when_the_file_is_missing() -> None:
    assert _StubRepository(present=False).query_if_file_exists("photo.jpg") is False
