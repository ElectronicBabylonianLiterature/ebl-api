from abc import ABC, abstractmethod


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
