from __future__ import annotations
import re
import attr
from itertools import chain
from typing import Sequence, Tuple, cast, Dict, Optional
from collections import OrderedDict
from ebl.errors import DataError
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.lark_parser import PARSE_ERRORS, parse_line
from ebl.transliteration.domain.text_line import TextLine


@attr.s(auto_attribs=True, frozen=True)
class TransliterationQuery:

    _sign_repository: SignRepository | None
    string: str
    wildcard_matchers: Dict[str, str] = OrderedDict(
        {
            "alternative": r"\[[^\]]*\|[^\]]*]",
            "any sign": r"\?",
            "any sign+": r"\*",
        }
    )

    def __init__(
        self, string: str, sign_repository: Optional[SignRepository] = None
    ) -> None:
        self._sign_repository = sign_repository or None
        self.string = string

    @property
    def regexp(self) -> str:
        string = self.string.strip(" -.\n")
        return self.children_regexp(string) if string else ""

    @property
    def type(self) -> str:
        return self.classify(self.string)

    def classify(self, string: str) -> str:
        if "\n" in string:
            return "lines"
        return next(
            (
                name
                for name, regex in self.wildcard_matchers.items()
                if re.match(regex, string)
            ),
            "text",
        )

    @property
    def all_wildcards(self) -> str:
        return r"|".join(f"({regexp})" for regexp in self.wildcard_matchers.values())

    def is_empty(self) -> bool:
        return not self.regexp

    def children_regexp(self, string: str = "") -> str:
        children = self.create_children(string)
        separator = (
            r"( .*)?\n.*" if children != [] and children[0].type == "line" else ""
        )
        return rf"{separator}".join(child.regexp for child in children)

    def create_children(self, string: str = "") -> Sequence[TransliterationQuery]:
        children: Sequence[TransliterationQuery] = []
        if not string:
            string = self.string
        for segment in [seg for seg in re.split(self.all_wildcards, string) if seg]:
            segment_type = self.classify(segment)
            if segment_type == "lines":
                children += [
                    self.make_transliteration_query_line(line)
                    for line in segment.split("\n")
                ]
            elif segment_type == "text":
                children += [self.make_transliteration_query_text(segment)]
            else:
                children += [self.make_transliteration_query_wildcard(segment)]
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

    def _standardize_transliteration(self, transliteration: str) -> str:
        return "\n".join(
            " ".join(self._create_signs(line)) for line in transliteration.split("\n")
        )

    def _create_signs(self, string: str = "") -> Sequence[str]:
        if not self._sign_repository:
            return []
        string = string or self.string
        visitor = SignsVisitor(self._sign_repository)
        self._parse_line(string).accept(visitor)
        return visitor.result

    def create_sign_regexp(self, sign: str) -> str:
        return rf"([^\s]+\/)*{re.escape(sign)}(\/[^\s]+)*"

    def _parse_line(self, line: str) -> TextLine:
        line = line.strip(" -.")
        try:
            return cast(TextLine, parse_line(f"1. {line}"))
        except PARSE_ERRORS:
            raise DataError("Invalid transliteration query.")

    def make_transliteration_query_line(self, string: str) -> TransliterationQueryLine:
        return TransliterationQueryLine(
            string=string, sign_repository=self._sign_repository
        )

    def make_transliteration_query_text(self, string: str) -> TransliterationQueryText:
        return TransliterationQueryText(
            string=string, sign_repository=self._sign_repository
        )

    def make_transliteration_query_wildcard(
        self, string: str
    ) -> TransliterationQueryWildCard:
        return TransliterationQueryWildCard(
            string=string, sign_repository=self._sign_repository
        )


class TransliterationQueryText(TransliterationQuery):
    @property
    def regexp(self) -> str:
        signs_regexp = " ".join(
            self.create_sign_regexp(sign) for sign in self._create_signs()
        )
        return rf"(?<![^|\s]){signs_regexp}"


class TransliterationQueryWildCard(TransliterationQuery):
    @property
    def regexp(self) -> str:
        if self.type == "alternative":
            return self.regexp_alternative()
        if self.type == "any sign":
            return r"([^\s]+\/)*[^ ]+(\/[^\s]+)*"
        return r"([^\s]+\/)*[^ ]+(\/[^\s]+)*.*" if self.type == "any sign+" else ""

    def regexp_alternative(self) -> str:
        alternative_strings = self.string.strip("[]").split("|")
        alternative_queries = [
            "".join(child.regexp for child in self.create_children(alternative_string))
            for alternative_string in alternative_strings
        ]
        regexp = r"|".join(alternative_queries)
        return rf"(?:{regexp})"


class TransliterationQueryLine(TransliterationQuery):
    @property
    def regexp(self) -> str:
        return rf"(?<![^|\s]){self.children_regexp()}"

    @property
    def type(self) -> str:
        return "line"
