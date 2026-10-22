from abc import ABC, abstractmethod
from typing import Optional


class CacheRepository(ABC):
    @abstractmethod
    def has(self, cache_key: str) -> bool:
        raise NotImplementedError

    @abstractmethod
    def get(self, cache_key: str) -> dict:
        raise NotImplementedError

    @abstractmethod
    def set(self, cache_key: str, item: dict) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, cache_key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete_all(self, pattern: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def chapter_revision(self, chapter_key: str) -> Optional[int]:
        raise NotImplementedError

    @abstractmethod
    def start_chapter_update(self, chapter_key: str) -> None:
        raise NotImplementedError

    @abstractmethod
    def finish_chapter_update(self, chapter_key: str) -> None:
        raise NotImplementedError
