from enum import unique, Enum
from typing import FrozenSet, Set, AbstractSet


@unique
class EnclosureType(Enum):
    ACCIDENTAL_OMISSION = ("ACCIDENTAL_OMISSION", frozenset(["INTENTIONAL_OMISSION"]))
    INTENTIONAL_OMISSION = ("INTENTIONAL_OMISSION", frozenset(["ACCIDENTAL_OMISSION"]))
    REMOVAL = ("REMOVAL",)
    EMENDATION = "EMENDATION"
    BROKEN_AWAY = ("BROKEN_AWAY", frozenset(["PERHAPS_BROKEN_AWAY", "PERHAPS"]))
    PERHAPS_BROKEN_AWAY = (
        "PERHAPS_BROKEN_AWAY",
        frozenset(["PERHAPS", "ACCIDENTAL_OMISSION", "INTENTIONAL_OMISSION"]),
        frozenset(["BROKEN_AWAY"]),
    )
    PERHAPS = (
        "PERHAPS",
        frozenset(
            [
                "PERHAPS_BROKEN_AWAY",
                "BROKEN_AWAY",
                "ACCIDENTAL_OMISSION",
                "INTENTIONAL_OMISSION",
            ]
        ),
    )
    DOCUMENT_ORIENTED_GLOSS = ("DOCUMENT_ORIENTED_GLOSS",)

    def __init__(
        self,
        id_: str,
        forbidden: FrozenSet[str] = frozenset(),
        required: FrozenSet[str] = frozenset(),
    ):
        self._id = id_
        self._forbidden = forbidden.union({id_})
        self._required = required

    @property
    def required(self) -> Set["EnclosureType"]:
        return {EnclosureType[name] for name in self._required}

    @property
    def forbidden(self) -> Set["EnclosureType"]:
        return {EnclosureType[name] for name in self._forbidden}

    def does_not_forbid(self, enclosures: AbstractSet["EnclosureType"]) -> bool:
        return self.forbidden.isdisjoint(enclosures)

    def are_requirements_satisfied_by(
        self, enclosures: AbstractSet["EnclosureType"]
    ) -> bool:
        return self.required.issubset(enclosures)
