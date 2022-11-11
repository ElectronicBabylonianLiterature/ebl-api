from abc import ABC, abstractmethod


class CacheRepository(ABC):
    @abstractmethod
    def has(self, key: str) -> bool:
        ...

    @abstractmethod
    def get(self, key: str) -> dict:
        ...

    @abstractmethod
    def set(self, key: str, item: dict) -> None:
        ...

    @abstractmethod
    def delete(self, key: str) -> None:
        ...
