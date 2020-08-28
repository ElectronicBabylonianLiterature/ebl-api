from typing import MutableSequence, Optional, Sequence

import attr

from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.atf import VARIANT_SEPARATOR
from ebl.transliteration.domain.lark_parser import parse_compound_grapheme
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme, Divider, Grapheme, NamedSign, Number
)
from ebl.transliteration.domain.unknown_sign_tokens import UnknownSign
from ebl.transliteration.domain.sign import Sign, SignName
from ebl.transliteration.domain.tokens import Token, TokenVisitor, Variant
from ebl.transliteration.domain.standardization import (
    INVALID, is_splittable, Standardization, UNKNOWN
)
from ebl.transliteration.domain.word_tokens import Word
from ebl.errors import NotFoundError


@attr.s(auto_attribs=True)
class SignsVisitor(TokenVisitor):
    _sign_repository: SignRepository
    _is_deep: bool = True
    _standardizations: MutableSequence[Standardization] = attr.ib(
        init=False,
        factory=list
    )

    @property
    def result(self) -> Sequence[str]:
        return [
            standardization.get_value(self._is_deep)
            for standardization in self._standardizations
        ]

    def visit_word(self, word: Word) -> None:
        sub_visitor = SignsVisitor(self._sign_repository)
        for token in word.parts:
            token.accept(sub_visitor)
        self._standardizations.extend(sub_visitor._standardizations)

    def visit_unknown_sign(self, sign: UnknownSign) -> None:
        self._standardizations.append(UNKNOWN)

    def visit_named_sign(self, named_sign: NamedSign) -> None:
        sign_token: Optional[Token] = named_sign.sign
        if sign_token is None:
            sign: Optional[Sign] = self._sign_repository.search(named_sign.name.lower(),
                                                                named_sign.sub_index)
            (self._standardizations.append(INVALID)
             if sign is None
             else self._visit_sign(sign))
        else:
            sign_token.accept(self)

    def visit_number(self, number: Number) -> None:
        sign_token: Optional[Token] = number.sign
        if sign_token is None:
            sign: Optional[Sign] = self._sign_repository.search(number.name.lower(),
                                                                number.sub_index)
            (self._standardizations.append(Standardization.of_string(number.name))
             if sign is None
             else self._visit_sign(sign))
        else:
            sign_token.accept(self)

    def visit_compound_grapheme(self, grapheme: CompoundGrapheme) -> None:
        if self._is_deep and is_splittable(grapheme.name):
            standardizations: Sequence[Standardization] = [
                self._find(SignName(part))
                for part in grapheme.compound_parts
            ]
            self._standardizations.extend(standardizations)
        else:
            self._standardizations.append(self._find(grapheme.name))

    def visit_grapheme(self, grapheme: Grapheme) -> None:
        self._standardizations.append(self._find(grapheme.name))

    def visit_divider(self, divider: Divider) -> None:
        # | should not be handled as divider. It is not a value of any sign.
        # See: Editorial conventions (Corpus) 3.2.1.3 lines of tablet
        if divider.divider != "|":
            sign: Optional[Sign] = self._sign_repository.search(divider.divider, 1)
            (self._standardizations.append(INVALID)
             if sign is None
             else self._visit_sign(sign))

    def visit_variant(self, variant: Variant) -> None:
        variant_visitor = SignsVisitor(self._sign_repository, False)
        for token in variant.tokens:
            token.accept(variant_visitor)

        self._standardizations.append(
            Standardization.of_string(VARIANT_SEPARATOR.join(variant_visitor.result))
        )

    def _visit_sign(self, sign: Sign) -> None:
        if self._is_deep and is_splittable(sign.name):
            grapheme: CompoundGrapheme = parse_compound_grapheme(sign.name)
            grapheme.accept(self)
        else:
            self._standardizations.append(Standardization.of_sign(sign))

    def _find(self, name: SignName) -> Standardization:
        try:
            return Standardization.of_sign(self._sign_repository.find(name))
        except NotFoundError:
            return Standardization.of_string(name)
