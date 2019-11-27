from abc import ABC, abstractmethod


class User(ABC):
    @property
    @abstractmethod
    def profile(self) -> dict:
        ...

    @property
    @abstractmethod
    def ebl_name(self) -> str:
        ...

    def has_scope(self, scope: str) -> bool:
        return False

    def can_read_folio(self, name: str) -> bool:
        scope = f"read:{name}-folios"
        return self.has_scope(scope)


class Guest(User):
    @property
    def profile(self):
        return {"name": "Guest"}

    @property
    def ebl_name(self):
        return "Guest"


class ApiUser(User):
    def __init__(self, script_name: str):
        self._script_name = script_name

    @property
    def profile(self):
        return {"name": self._script_name}

    @property
    def ebl_name(self):
        return "Script"
