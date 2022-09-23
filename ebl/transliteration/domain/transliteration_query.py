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

"""
def create_sign_regexp(sign):
    return r"[^\s]+" if sign == "*" else rf"([^\s]+\/)*{re.escape(sign)}(\/[^\s]+)*"


def create_signs_fork_regexp(signs: Sequence):
    return (
        "(?:"
        + "".join([create_sign_regexp(sign) if sign != "|" else sign for sign in signs])
        + ")"
    )


def create_line_regexp(line):
    signs_regexp = " ".join(
        create_sign_regexp(sign)
        if type(sign) == str
        else create_signs_fork_regexp(sign)
        for sign in line
    )
    return rf"(?<![^|\s]){signs_regexp}"



def get_line_number(signs: str, position: int) -> int:
    return len([char for char in chain.from_iterable(signs[:position]) if char == "\n"])
"""


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

    def __init__(self, string: str, sign_repository: Optional[SignRepository]=None) -> None:
        self._sign_repository = sign_repository if sign_repository else None
        self.string = string

    @property
    def regexp(self) -> str:
        return self.children_regexp(self.string)

    @property
    def type(self) -> str:
        return self.classify(self.string)

    def classify(self, string: str) -> str:
        if "\n" in string:
            return "lines"
        for name, regex in self.wildcard_matchers.items():
            if re.match(regex, string):
                return name
        return "text"

    @property
    def all_wildcards(self) -> str:
        return r"|".join(f"({regexp})" for regexp in self.wildcard_matchers.values())

    def is_empty(self) -> bool:
        return self.regexp == r""

    def children_regexp(self, string: str = '') -> str:
        return r"".join(child.regexp for child in self.create_children(string))

    def create_children(self, string: str = '') -> Sequence[TransliterationQuery]:
        children: Sequence[TransliterationQuery] = []
        if not string:
            string = self.string
        for segment in [
            seg for seg in re.split(self.all_wildcards, string) if seg
        ]:
            segment_type = self.classify(segment)
            if segment_type == "lines":
                children += [
                    self.make_transliteration_query_line(line)
                    for line in segment.split("\n")
                ]
            elif segment_type != "text":
                children += [self.make_transliteration_query_wildcard(segment)]
            else:
                children += [self.make_transliteration_query_text(segment)]
        return children

    def match(self, signs: str) -> Sequence[Tuple[int, int]]:
        return [
            (
                self.get_line_number(signs, match.start()),
                self.get_line_number(signs, match.end()),
            )
            for match in re.finditer(self.regexp, signs)
        ]

    def get_line_number(self, signs: str, position: int) -> int:
        return len(
            [char for char in chain.from_iterable(signs[:position]) if char == "\n"]
        )

    def _create_signs(self) -> Sequence[str]:
        if not self._sign_repository:
            return []
        visitor = SignsVisitor(self._sign_repository)
        self._parse_line(self.string).accept(visitor)
        print(visitor)
        print(visitor.result)
        return visitor.result

    def create_sign_regexp(self, sign: str) -> str:
        return rf"([^\s]+\/)*{re.escape(sign)}(\/[^\s]+)*"

    def _parse_line(self, line: str) -> TextLine:
        line = line.strip(' -.')
        print(['!', line])
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

    def make_transliteration_query_wildcard(self, string: str) -> TransliterationQueryWildCard:
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
            alternative_strings = self.string.strip("[]").split("|")
            for alt_string in alternative_strings:
                self.create_children(alt_string)
            return r"WC alt"
        if self.type == "any sign":
            return r"WC any"
        if self.type == "any sign+":
            return r"WC any\+"
        return ""


class TransliterationQueryLine(TransliterationQuery):

    @property
    def regexp(self) -> str:
        return rf"(?<![^|\s]){self.children_regexp()}"
