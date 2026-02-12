from abc import ABC, abstractmethod
from typing import Any, Mapping
from ebl.common.domain.scopes import Scope

from ebl.errors import NotFoundError
from ebl.users.domain.user import User


class File(ABC):
    @property
    @abstractmethod
    def metadata(self) -> Mapping[str, Any]: ...

    @property
    @abstractmethod
    def length(self) -> int: ...

    @property
    @abstractmethod
    def content_type(self) -> str: ...

    @abstractmethod
    def read(self, size=-1) -> bytes: ...

    @abstractmethod
    def close(self) -> None: ...

    def can_be_read_by(self, user: User):
        scope = Scope.from_string(f"read:{self.metadata.get('scope')}")
        return not scope or user.has_scope(scope)


class FileRepository(ABC):
    @abstractmethod
    def query_by_file_name(self, file_name: str) -> File: ...

    def query_if_file_exists(self, file_name: str) -> bool:
        try:
            self.query_by_file_name(file_name)
            return True
        except NotFoundError:
            return False
