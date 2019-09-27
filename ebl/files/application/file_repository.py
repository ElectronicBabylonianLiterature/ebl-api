from abc import ABC, abstractmethod
from typing import Any, Mapping

from ebl.auth0 import User


class File(ABC):
    @property
    @abstractmethod
    def metadata(self) -> Mapping[str, Any]:
        ...

    @property
    @abstractmethod
    def length(self) -> int:
        ...

    @property
    @abstractmethod
    def content_type(self) -> str:
        ...

    @abstractmethod
    def read(self, size: int) -> bytes:
        ...

    @abstractmethod
    def close(self) -> None:
        ...

    def can_be_read_by(self, user: User):
        scope = self.metadata.get('scope')
        return not scope or user.has_scope(f'read:{scope}')


class FileRepository(ABC):
    @abstractmethod
    def query_by_file_name(self, file_name: str) -> File:
        ...
