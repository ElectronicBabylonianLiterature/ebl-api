from abc import ABC, abstractmethod
from typing import Sequence, List, Optional


class User(ABC):
    hidden_scopes = [
        "read:ILF-folios",
        "read:SP-folios",
        "read:USK-folios",
        "read:ARG-folios",
        "read:WRM-folios",
        "read:MJG-folios",
        "read:SP-folios",
        "read:UG-folios",
        "read:SJL-folios",
        "read:EVW-folios",
    ]

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

    def is_hidden_folio_scope(self, scope: str) -> bool:
        return scope in self.hidden_scopes

    def can_read_folio(self, name: str) -> bool:
        scope = f"read:{name}-folios"
        return self.has_scope(scope) or not self.is_hidden_folio_scope(scope)

    def can_read_fragment(self, scopes: Sequence[str]) -> bool:
        return (not scopes) or any(
            self.has_scope(f"read:{scope}-fragments") for scope in scopes
        )

    def get_scopes(
        self, prefix: Optional[str] = "", suffix: Optional[str] = ""
    ) -> List[str]:
        return []


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
