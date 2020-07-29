from typing import MutableSequence, Sequence, Optional

import attr

from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.sign_tokens import CompoundGrapheme, NamedSign
from ebl.transliteration.domain.sign import Sign
from ebl.transliteration.domain.tokens import TokenVisitor
from ebl.transliteration.domain.standardization import Standardization
from ebl.transliteration.domain.word_tokens import Word


@attr.s(auto_attribs=True)
class SignsVisitor(TokenVisitor):
    _sign_repository: SignRepository
    _signs: MutableSequence[Optional[Sign]] = attr.ib(init=False, factory=list)

    @property
    def result(self) -> Sequence[str]:
        return [
            Standardization.of_sign(sign).get_value(True) if sign is not None else "?"
            for sign in self._signs
        ]

    def visit_named_sign(self, named_sign: NamedSign) -> None:
        sign: Optional[Sign] = self._sign_repository.search(named_sign.name.lower(),
                                                            named_sign.sub_index)
        self._signs.append(sign)

    def visit_word(self, word: Word) -> None:
        sub_visitor = SignsVisitor(self._sign_repository)
        for token in word.parts:
            token.accept(sub_visitor)
        self._signs.extend(sub_visitor._signs)

    def visit_compound_grapheme(self, grapheme: CompoundGrapheme) -> None:
        sign: Optional[Sign] = self._sign_repository.find(grapheme.name)
        self._signs.append(sign)
