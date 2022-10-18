from abc import ABC, abstractmethod
from typing import Sequence


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

    def can_read_fragment(self, scopes: Sequence[str]) -> bool:
        for scope_group in scopes:
            scope = f"read:{scope_group}-fragments"
            if not self.has_scope(scope):
                return False
        return True


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


class AtfImporterUser(User):
    def __init__(self, name: str):
        self.name = name

    @property
    def profile(self):
        return {"name": self.name}

    @property
    def ebl_name(self):
        return self.name
