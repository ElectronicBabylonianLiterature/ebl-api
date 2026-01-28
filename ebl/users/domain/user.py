from abc import ABC, abstractmethod
from typing import Sequence, List, Optional

from ebl.common.domain.scopes import Scope


class User(ABC):
    @property
    @abstractmethod
    def profile(self) -> dict: ...

    @property
    @abstractmethod
    def ebl_name(self) -> str: ...

    def has_scope(self, scope: Scope) -> bool:
        return scope.is_open

    def can_read_folio(self, name: str) -> bool:
        try:
            scope = Scope.from_string(f"read:{name}-folios")
            return self.has_scope(scope) or scope.is_open
        except ValueError:
            return True

    def can_read_fragment(self, fragment_scopes: Sequence[Scope]) -> bool:
        return (not fragment_scopes) or bool(
            set(self.get_scopes(prefix="read:", suffix="-fragments")).intersection(
                fragment_scopes
            )
        )

    def get_scopes(
        self, prefix: Optional[str] = "", suffix: Optional[str] = ""
    ) -> List[Scope]:
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
