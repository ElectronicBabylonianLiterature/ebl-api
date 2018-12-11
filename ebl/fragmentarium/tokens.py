from typing import Any


class Token():
    def __init__(self, value: str):
        self.__value = value

    @property
    def value(self) -> str:
        return self.__value

    @property
    def lemmatizable(self) -> bool:
        return False

    def __eq__(self, other: Any) -> bool:
        return isinstance(other, Token) and (self.value == other.value)

    def __hash__(self) -> int:
        return hash(self.value)

    def __repr__(self) -> str:
        return f'Token("{self.value}")'

    def __str__(self) -> str:
        return self.value
