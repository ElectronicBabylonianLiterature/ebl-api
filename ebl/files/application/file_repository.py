from abc import ABC, abstractmethod
from typing import Any, Mapping
from ebl.common.domain.scopes import Scope

from ebl.errors import NotFoundError
from ebl.users.domain.user import User


class File(ABC):
    @property
    @abstractmethod
    def metadata(self) -> Mapping[str, Any]:
        raise NotImplementedError

    @property
    @abstractmethod
    def length(self) -> int:
        raise NotImplementedError

    @property
    @abstractmethod
    def content_type(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def read(self, size=-1) -> bytes:
        raise NotImplementedError

    @abstractmethod
    def close(self) -> None:
        raise NotImplementedError

    def can_be_read_by(self, user: User):
        scope = Scope.from_string(f"read:{self.metadata.get('scope')}")
        return not scope or user.has_scope(scope)


class FileRepository(ABC):
    @abstractmethod
    def query_by_file_name(self, file_name: str) -> File:
        raise NotImplementedError

    def query_if_file_exists(self, file_name: str) -> bool:
        try:
            self.query_by_file_name(file_name)
            return True
        except NotFoundError:
            return False
