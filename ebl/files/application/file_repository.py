from abc import ABC, abstractmethod
from typing import Any, Mapping

from ebl.errors import NotFoundError


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
