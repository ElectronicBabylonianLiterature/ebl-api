import re
from typing import Callable, MutableSequence, Optional, Sequence, TypeVar, Union

import attr

from pydash import flat_map_deep

from ebl.errors import NotFoundError
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.atf import Flag, VARIANT_SEPARATOR
from ebl.transliteration.domain.enclosure_tokens import Gloss
from ebl.transliteration.domain.enclosure_type import EnclosureType
from ebl.transliteration.domain.atf_parsers.lark_parser import (
    parse_compound_grapheme,
    parse_reading,
)
from ebl.transliteration.domain.lark_parser_errors import PARSE_ERRORS
from ebl.transliteration.domain.sign import Sign, SignName
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Divider,
    Grapheme,
    NamedSign,
    Number,
)
from ebl.transliteration.domain.standardization import (
    INVALID,
    is_splittable,
    Standardization,
    UNKNOWN,
)
from ebl.transliteration.domain.tokens import ErasureState, Token, TokenVisitor, Variant
from ebl.transliteration.domain.unknown_sign_tokens import UnknownSign
from ebl.transliteration.domain.word_tokens import Word


def strip_flags(name: str) -> str:
    pattern = f"[{''.join([re.escape(flag.value) for flag in Flag])}]"
    return re.sub(pattern, "", name)


S = TypeVar("S")
T = TypeVar("T", bound=Token)


def skip_enclosures(func: Callable[[S, T], None]) -> Callable[[S, T], None]:
    skipped_enclosures = {
        EnclosureType.REMOVAL,
        EnclosureType.ACCIDENTAL_OMISSION,
        EnclosureType.INTENTIONAL_OMISSION,
    }

    def inner(self: S, token: T) -> None:
        if token.enclosure_type.isdisjoint(skipped_enclosures):
            func(self, token)

    return inner


def skip_erasures(func: Callable[[S, T], None]) -> Callable[[S, T], None]:
    def inner(self: S, token: T) -> None:
        if token.erasure != ErasureState.ERASED:
            func(self, token)

    return inner


@attr.s(auto_attribs=True)
class SignsVisitor(TokenVisitor):
    _sign_repository: SignRepository
    _is_deep: bool = True
    _to_unicode: bool = False
    _standardizations: MutableSequence[Standardization] = attr.ib(
        init=False, factory=list
    )

    @property
    def result(self) -> Sequence[Union[int, str]]:
        return self.result_unicode if self._to_unicode else self.result_string

    @property
    def result_string(self) -> Sequence[str]:
        return [
            standardization.get_value(self._is_deep)
            for standardization in self._standardizations
        ]

    @property
    def result_unicode(self) -> Sequence[int]:
        return flat_map_deep(
            [standardization.unicode for standardization in self._standardizations]
        )

    @skip_erasures
    def visit_word(self, word: Word) -> None:
        self._visit_tokens(word.parts)

    def visit_gloss(self, gloss: Gloss) -> None:
        self._visit_tokens(gloss.parts)

    @skip_erasures
    @skip_enclosures
    def visit_unknown_sign(self, sign: UnknownSign) -> None:
        self._standardizations.append(UNKNOWN)

    @skip_erasures
    @skip_enclosures
    def visit_named_sign(self, named_sign: NamedSign) -> None:
        sign_token: Optional[Token] = named_sign.sign
        if sign_token is None:
            sign: Optional[Sign] = self._sign_repository.search(
                named_sign.name.lower(), named_sign.sub_index
            )
            (
                self._standardizations.append(INVALID)
                if sign is None
                else self._visit_sign(sign)
            )
        else:
            sign_token.accept(self)

    @skip_erasures
    @skip_enclosures
    def visit_number(self, number: Number) -> None:
        sign_token: Optional[Token] = number.sign
        if sign_token is None:
            sign: Optional[Sign] = self._sign_repository.search(
                number.name.lower(), number.sub_index
            )
            (
                self._standardizations.append(Standardization.of_string(number.name))
                if sign is None
                else self._visit_sign(sign)
            )
        else:
            sign_token.accept(self)

    @skip_erasures
    @skip_enclosures
    def visit_compound_grapheme(self, grapheme: CompoundGrapheme) -> None:
        if self._is_deep and is_splittable(grapheme.name):
            for part in grapheme.compound_parts:
                self._visit_compount_grapheme_part(strip_flags(part))
        else:
            self._standardizations.append(
                self._find(SignName(strip_flags(grapheme.name)))
            )

    def _visit_compount_grapheme_part(self, stripped_part: str) -> None:
        try:
            reading = parse_reading(stripped_part.lower())
            self.visit_named_sign(reading)
            if self._standardizations[-1] == INVALID:
                self._standardizations[-1] = self._find(SignName(stripped_part))
        except PARSE_ERRORS:
            self._standardizations.append(self._find(SignName(stripped_part)))

    def visit_grapheme(self, grapheme: Grapheme) -> None:
        self._standardizations.append(self._find(grapheme.name))

    @skip_erasures
    @skip_enclosures
    def visit_divider(self, divider: Divider) -> None:
        sign: Optional[Sign] = self._sign_repository.search(divider.divider, 1)
        (
            self._standardizations.append(INVALID)
            if sign is None
            else self._visit_sign(sign)
        )

    @skip_erasures
    @skip_enclosures
    def visit_variant(self, variant: Variant) -> None:
        variant_visitor = SignsVisitor(self._sign_repository, False, self._to_unicode)
        tokens_len = len(variant.tokens)
        for index, token in enumerate(variant.tokens):
            token.accept(variant_visitor)
            if index + 1 < tokens_len and self._to_unicode:
                variant_visitor._standardizations.append(
                    Standardization.of_string(VARIANT_SEPARATOR)
                )
        self._visit_variant(variant_visitor)

    def _visit_variant(self, variant_visitor: "SignsVisitor") -> None:
        if not self._to_unicode:
            self._standardizations.append(
                Standardization.of_string(
                    VARIANT_SEPARATOR.join(variant_visitor.result_string)
                )
            )
        else:
            self._standardizations += variant_visitor._standardizations

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

    def _visit_tokens(self, tokens: Sequence[Token]) -> None:
        sub_visitor = SignsVisitor(
            self._sign_repository, self._is_deep, self._to_unicode
        )
        for token in tokens:
            token.accept(sub_visitor)
        self._standardizations.extend(sub_visitor._standardizations)
