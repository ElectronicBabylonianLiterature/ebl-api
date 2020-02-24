from enum import Enum, unique
from functools import singledispatchmethod  # type: ignore
from typing import FrozenSet, Set

from ebl.transliteration.domain.enclosure_error import EnclosureError
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    IntentionalOmission,
    Removal,
    BrokenAway,
    PerhapsBrokenAway,
    DocumentOrientedGloss,
)
from ebl.transliteration.domain.tokens import (
    Token,
    TokenVisitor,
)
from ebl.transliteration.domain.word_tokens import (
    Word,
)


@unique
class EnclosureType(Enum):
    ACCIDENTAL_OMISSION = (
        "ACCIDENTAL_OMISSION",
        frozenset(["ACCIDENTAL_OMISSION", "INTENTIONAL_OMISSION"]),
    )
    INTENTIONAL_OMISSION = (
        "INTENTIONAL_OMISSION",
        frozenset(["INTENTIONAL_OMISSION", "ACCIDENTAL_OMISSION"]),
    )
    REMOVAL = ("REMOVAL", frozenset(["REMOVAL"]))
    BROKEN_AWAY = ("BROKEN_AWAY", frozenset(["BROKEN_AWAY", "PERHAPS_BROKEN_AWAY"]))
    PERHAPS_BROKEN_AWAY = (
        "PERHAPS_BROKEN_AWAY",
        frozenset(["PERHAPS_BROKEN_AWAY"]),
        frozenset(["BROKEN_AWAY"]),
    )
    DOCUMENT_ORIENTED_GLOSS = (
        "DOCUMENT_ORIENTED_GLOSS",
        frozenset(["DOCUMENT_ORIENTED_GLOSS"]),
    )

    def __init__(
        self,
        id_: str,
        forbidden: FrozenSet[str] = frozenset(),
        required: FrozenSet[str] = frozenset(),
    ):
        self._id = id_
        self.forbidden = forbidden
        self.required = required


class EnclosureVisitor(TokenVisitor):
    def __init__(self):
        self._enclosures: Set[str] = set()

    def done(self):
        if len(self._enclosures) > 0:
            raise EnclosureError()

    @singledispatchmethod
    def visit(self, token: Token) -> None:
        pass

    @visit.register
    def _visit_word(self, token: Word) -> None:
        for part in token.parts:
            part.accept(self)

    @visit.register
    def _visit_accidental_omission(self, token: AccidentalOmission) -> None:
        if token == AccidentalOmission.open():
            self._open(EnclosureType.ACCIDENTAL_OMISSION)
        else:
            self._close(EnclosureType.ACCIDENTAL_OMISSION)

    @visit.register
    def _visit_intentional_omission(self, token: IntentionalOmission) -> None:
        if token == IntentionalOmission.open():
            self._open(EnclosureType.INTENTIONAL_OMISSION)
        else:
            self._close(EnclosureType.INTENTIONAL_OMISSION)

    @visit.register
    def _visit_removal(self, token: Removal) -> None:
        if token == Removal.open():
            self._open(EnclosureType.REMOVAL)
        else:
            self._close(EnclosureType.REMOVAL)

    @visit.register
    def _visit_broken_away(self, token: BrokenAway) -> None:
        if token == BrokenAway.open():
            self._open(EnclosureType.BROKEN_AWAY)
        else:
            self._close(EnclosureType.BROKEN_AWAY)

    @visit.register
    def _visit_perhaps_broken_away(self, token: PerhapsBrokenAway) -> None:
        if token == PerhapsBrokenAway.open():
            self._open(EnclosureType.PERHAPS_BROKEN_AWAY)
        else:
            self._close(EnclosureType.PERHAPS_BROKEN_AWAY)

    @visit.register
    def _visit_document_oriented_gloss(self, token: DocumentOrientedGloss) -> None:
        if token == DocumentOrientedGloss.open():
            self._open(EnclosureType.DOCUMENT_ORIENTED_GLOSS)
        else:
            self._close(EnclosureType.DOCUMENT_ORIENTED_GLOSS)

    def _open(self, enclosure: EnclosureType):
        if self._is_allowed_to_open(enclosure):
            self._enclosures.add(enclosure.name)
        else:
            raise EnclosureError()

    def _close(self, enclosure: EnclosureType):
        if self._is_allowed_to_close(enclosure):
            self._enclosures.remove(enclosure.name)
        else:
            raise EnclosureError()

    def _is_allowed_to_open(self, enclosure: EnclosureType) -> bool:
        return enclosure.forbidden.isdisjoint(
            self._enclosures
        ) and enclosure.required.issubset(self._enclosures)

    def _is_allowed_to_close(self, enclosure: EnclosureType) -> bool:
        return enclosure.name in self._enclosures
