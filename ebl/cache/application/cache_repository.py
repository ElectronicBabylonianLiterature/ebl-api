from abc import ABC, abstractmethod


class CacheRepository(ABC):
    @abstractmethod
    def has(self, cache_key: str) -> bool:
        ...

    @abstractmethod
    def get(self, cache_key: str) -> dict:
        ...

    @abstractmethod
    def set(self, cache_key: str, item: dict) -> None:
        ...

    @abstractmethod
    def delete(self, cache_key: str) -> None:
        ...

    @abstractmethod
    def delete_all(self, pattern: str) -> None:
        ...
