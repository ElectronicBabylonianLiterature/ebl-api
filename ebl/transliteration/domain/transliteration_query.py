from __future__ import annotations
import re
import attr
from itertools import chain
from typing import cast, Sequence, Tuple, List, Optional
from enum import Enum
from collections import OrderedDict
from ebl.errors import DataError
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.lark_parser import PARSE_ERRORS, parse_line
from ebl.transliteration.domain.text_line import TextLine


class Type(Enum):
    UNDEFINED = None
    LINES = "lines"
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
    sign_repository: Optional[SignRepository]
    type: Type = attr.ib(init=False)
    regexp: str = attr.ib(init=False)

    def __attrs_post_init__(self) -> None:
        self.type = self._classify(self.string)
        self.regexp = self._regexp()

    def _regexp(self) -> str:
        string = self.string.strip(" -.\n")
        return self.children_regexp(string) if string else ""

    def _classify(self, string: str) -> Type:
        if "\n" in string:
            return Type.LINES
        return next(
            (
                type
                for type, regex in wildcard_matchers.items()
                if re.match(regex, string)
            ),
            Type.TEXT,
        )

    @property
    def all_wildcards(self) -> str:
        return r"|".join(f"({regexp})" for regexp in wildcard_matchers.values())

    def is_empty(self) -> bool:
        return not self.regexp

    def children_regexp(self, string: str = "", lines: bool = False) -> str:
        children = self.create_children(string)
        if children == []:
            return r""
        separator = r"( .*)?\n.*" if self.type == Type.LINES else " "
        return rf"{separator}".join(child.regexp for child in children)

    def create_children(self, string: str = "") -> Sequence[TransliterationQuery]:
        if not string:
            string = self.string
        segments = [seg for seg in re.split(self.all_wildcards, string) if seg]
        return self.get_children_from_segments(segments)

    def get_children_from_segments(
        self, segments: Sequence[str]
    ) -> List[TransliterationQuery]:
        children: List[TransliterationQuery] = []
        for segment in segments:
            segment_type = self._classify(segment)
            if segment_type == Type.LINES:
                children.extend(
                    self.make_transliteration_query_line(line)
                    for line in segment.split("\n")
                )
            elif segment_type in wildcard_matchers:
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
        return len(
            [
                char
                for char in chain.from_iterable(transliteration[:position])
                if char == "\n"
            ]
        )

    def make_transliteration_query_line(self, string: str) -> TransliterationQueryLine:
        return TransliterationQueryLine(
            string=string, sign_repository=self.sign_repository
        )

    def make_transliteration_query_text(self, string: str) -> TransliterationQueryText:
        return TransliterationQueryText(
            string=string, sign_repository=self.sign_repository
        )

    def make_transliteration_query_wildcard(
        self, string: str
    ) -> TransliterationQueryWildCard:
        return TransliterationQueryWildCard(
            string=string, sign_repository=self.sign_repository
        )


@attr.s(auto_attribs=True)
class TransliterationQueryText(TransliterationQuery):
    def _regexp(self) -> str:
        signs_regexp = " ".join(
            self._create_sign_regexp(sign) for sign in self._create_signs(self.string)
        )
        return rf"(?<![^|\s]){signs_regexp}"

    def _create_sign_regexp(self, sign: str) -> str:
        return rf"([^\s]+\/)*{re.escape(sign)}(\/[^\s]+)*"

    def _create_signs(self, transliteration: str) -> Sequence[str]:
        if not self.sign_repository:
            return []
        visitor = SignsVisitor(self.sign_repository)
        self._parse(transliteration).accept(visitor)
        
        return visitor.result

    def _parse(self, transliteration: str) -> TextLine:
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
        if self.type == Type.ANY_SIGN:
            return r"([^\s]+\/)*[^ ]+(\/[^\s]+)*"
        return (
            r"([^\s]+\/)*[^ ]+(\/[^\s]+)*.*" if self.type == Type.ANY_SIGN_PLUS else ""
        )

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
    def _regexp(self) -> str:
        return rf"(?<![^|\s]){self.children_regexp(self.string, True)}"
