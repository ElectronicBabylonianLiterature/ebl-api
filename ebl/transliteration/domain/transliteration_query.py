from __future__ import annotations
import re
import attr
from typing import cast, Sequence, Tuple, List
from enum import Enum
from collections import OrderedDict
from ebl.errors import DataError
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_line
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import TokenVisitor


class Type(Enum):
    UNDEFINED = None
    LINES = "lines"
    LINE = "line"
    TEXT = "text"
    ALTERNATIVE = "alternative"
    ANY_SIGN = "any sign"
    ANY_SIGN_PLUS = "any sign+"


wildcard_matchers: OrderedDict[Type, str] = OrderedDict(
    {
        Type.ALTERNATIVE: r"\[[^\]]*\|[^\]]*]",
        Type.ANY_SIGN: r"\?",
        Type.ANY_SIGN_PLUS: r"\*",
    }
)


@attr.s(auto_attribs=True)
class TransliterationQuery:
    string: str
    visitor: TokenVisitor
    type: Type = attr.ib(init=False)
    regexp: str = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        self.string = self.string.strip(" -.\n")
        self.type = self._classify(self.string)
        self.regexp = self._regexp()

    def _regexp(self) -> str:
        return r"" if self.is_empty() else self.children_regexp(self.string)

    def _classify(self, string: str) -> Type:
        if not string:
            return Type.UNDEFINED
        if "\n" in string:
            return Type.LINES
        return next(
            (
                type
                for type, regex in wildcard_matchers.items()
                if re.match(rf"^{regex}$", string)
            ),
            Type.TEXT,
        )

    @property
    def all_wildcards(self) -> str:
        return r"|".join(f"({regexp})" for regexp in wildcard_matchers.values())

    def is_empty(self) -> bool:
        return self.type == Type.UNDEFINED or not self.string

    def children_regexp(self, string: str = "") -> str:
        children = self.create_children(string)
        if not children:
            return r""
        separator = r"( .*)?\n.*" if self.type == Type.LINES else r" "
        return separator.join(child.regexp for child in children)

    def create_children(self, string: str = "") -> Sequence[TransliterationQuery]:
        return (
            [self.make_transliteration_query_line(line) for line in string.split("\n")]
            if self.type == Type.LINES
            else self.create_inline_children(string)
        )

    def create_inline_children(
        self, string: str = ""
    ) -> Sequence[TransliterationQuery]:
        if not string:
            string = self.string
        segments = [
            seg.strip(" -.")
            for seg in re.split(self.all_wildcards, string)
            if seg and seg.strip(" -.")
        ]
        return self.get_children_from_segments(segments)

    def get_children_from_segments(
        self, segments: Sequence[str]
    ) -> List[TransliterationQuery]:
        children: List[TransliterationQuery] = []
        for segment in segments:
            segment_type = self._classify(segment)
            if segment_type in wildcard_matchers:
                children.append(self.make_transliteration_query_wildcard(segment))
            else:
                children.append(self.make_transliteration_query_text(segment))
        return children

    def match(self, transliteration: str) -> Sequence[Tuple[int, int]]:
        return [
            (
                self.get_line_number(transliteration, match.start()),
                self.get_line_number(transliteration, match.end()),
            )
            for match in re.finditer(
                re.compile(self.regexp, re.MULTILINE), transliteration
            )
        ]

    def get_line_number(self, transliteration: str, position: int) -> int:
        return transliteration[:position].count("\n")

    def make_transliteration_query_line(self, string: str) -> TransliterationQueryLine:
        return TransliterationQueryLine(string=string, visitor=self.visitor)

    def make_transliteration_query_text(self, string: str) -> TransliterationQueryText:
        return TransliterationQueryText(string=string, visitor=self.visitor)

    def make_transliteration_query_wildcard(
        self, string: str
    ) -> TransliterationQueryWildCard:
        return TransliterationQueryWildCard(string=string, visitor=self.visitor)


@attr.s(auto_attribs=True)
class TransliterationQueryText(TransliterationQuery):
    def _regexp(self) -> str:
        signs_regexp = " ".join(
            self._create_sign_regexp(sign) for sign in self._create_signs(self.string)
        )
        return rf"(?<![^|\s]){signs_regexp}"

    def _create_sign_regexp(self, sign: str) -> str:
        return rf"(\S+\/)*{re.escape(sign)}(?![^\s\/])"

    def _create_signs(self, transliteration: str) -> Sequence[str]:
        if not transliteration:
            return []
        self.visitor._standardizations = []
        self._parse(transliteration).accept(self.visitor)
        return self.visitor.result

    def _parse(self, transliteration: str) -> TextLine:
        from ebl.transliteration.domain.lark_parser_errors import PARSE_ERRORS

        transliteration = transliteration.strip(" -.")
        try:
            return cast(TextLine, parse_line(f"1. {transliteration}"))
        except PARSE_ERRORS:
            raise DataError("Invalid transliteration query.")


@attr.s(auto_attribs=True)
class TransliterationQueryWildCard(TransliterationQuery):
    def _regexp(self) -> str:
        if self.type == Type.ALTERNATIVE:
            return self._regexp_alternative()

        any_sign_regex = r"(\S+\/)*[^ ]+(\/\S+)*"

        if self.type == Type.ANY_SIGN:
            return any_sign_regex

        return f"{any_sign_regex}.*" if self.type == Type.ANY_SIGN_PLUS else ""

    def _regexp_alternative(self) -> str:
        alternative_strings = self.string.strip("[]").split("|")
        alternative_queries = [
            "".join(child.regexp for child in self.create_children(alternative_string))
            for alternative_string in alternative_strings
        ]
        regexp = r"|".join(alternative_queries)
        return rf"({regexp})"


@attr.s(auto_attribs=True)
class TransliterationQueryLine(TransliterationQuery):
    def _classify(self, string: str) -> Type:
        return Type.LINE

    def _regexp(self) -> str:
        content = TransliterationQuery(string=self.string, visitor=self.visitor)
        return rf"(?<![^|\s]){content.regexp}"


@attr.s(auto_attribs=True, frozen=True)
class TransliterationQueryEmpty(TransliterationQuery):
    string: str = ""
    visitor: TokenVisitor = TokenVisitor()
    type: Type = Type.UNDEFINED
    regexp: str = r""

    def __attrs_post_init__(self) -> None:
        pass
