from typing import MutableSequence, Sequence, Optional

import attr

from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.lark_parser import parse_compound_grapheme
from ebl.transliteration.domain.sign_tokens import CompoundGrapheme, NamedSign
from ebl.transliteration.domain.sign import Sign, SignName
from ebl.transliteration.domain.tokens import TokenVisitor
from ebl.transliteration.domain.standardization import is_splittable, Standardization
from ebl.transliteration.domain.word_tokens import Word
from ebl.errors import NotFoundError


@attr.s(auto_attribs=True)
class SignsVisitor(TokenVisitor):
    _sign_repository: SignRepository
    _standardizations: MutableSequence[Optional[Standardization]] = attr.ib(
        init=False,
        factory=list
    )

    @property
    def result(self) -> Sequence[str]:
        return [
            sign.get_value(True) if sign is not None else "?"
            for sign in self._standardizations
        ]

    def visit_named_sign(self, named_sign: NamedSign) -> None:
        sign: Optional[Sign] = self._sign_repository.search(named_sign.name.lower(),
                                                            named_sign.sub_index)
        if sign is None:
            self._standardizations.append(sign)
        else:
            self._visit_sign(sign)

    def visit_word(self, word: Word) -> None:
        sub_visitor = SignsVisitor(self._sign_repository)
        for token in word.parts:
            token.accept(sub_visitor)
        self._standardizations.extend(sub_visitor._standardizations)

    def visit_compound_grapheme(self, grapheme: CompoundGrapheme) -> None:
        if is_splittable(grapheme.name):
            standardizations: Sequence[Standardization] = [
                self._find(SignName(part))
                for part in grapheme.compound_parts
            ]
            self._standardizations.extend(standardizations)
        else:
            self._standardizations.append(self._find(grapheme.name))

    def _visit_sign(self, sign: Sign) -> None:
        if is_splittable(sign.name):
            grapheme: CompoundGrapheme = parse_compound_grapheme(sign.name)
            grapheme.accept(self)
        else:
            self._standardizations.append(Standardization.of_sign(sign))

    def _find(self, name: SignName) -> Standardization:
        try:
            return Standardization.of_sign(self._sign_repository.find(name))
        except NotFoundError:
            return Standardization.of_string(name)
