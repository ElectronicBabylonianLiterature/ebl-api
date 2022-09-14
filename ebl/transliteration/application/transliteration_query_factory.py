from typing import Sequence, cast
import re

from ebl.errors import DataError
from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.lark_parser import PARSE_ERRORS, parse_line
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.transliteration_query import TransliterationQuery


class TransliterationQueryFactory:
    def __init__(self, sign_repositoy: SignRepository) -> None:
        self._sign_repositoy = sign_repositoy

    @staticmethod
    def create_empty() -> TransliterationQuery:
        return TransliterationQuery([])

    def create(self, transliteration: str) -> TransliterationQuery:
        print('! t !', transliteration)
        # ToDo:
        # - Introduce wildcards here
        #    - A new class / classes might be practical (?)
        #    - Types are:
        #       - ? = any one sign
        #       - [a|b] = alternative signs (e.g. [bu|ba])
        #       - * = any sign or sequence of signs before a \n
        signs = [self._create_signs(line) for line in transliteration.split("\n")]
        return TransliterationQuery(signs)

    def _create_signs(self, line: str) -> Sequence[str]:
        visitor = SignsVisitor(self._sign_repositoy)
        self._parse_line(line).accept(visitor)

        return visitor.result

    def _parse_line(self, line: str) -> TextLine:
        # ToDo:
        # - Check if implementing regex here for wildcards is reasonable (`TextLine` serialization might make this hardly possible).
        # - If regex is not a solution, rearrange to generate a list of line variants that is passed to the query.
        # - Another, hybrid approach would be generating regex from a list of `TextLine` for the mongo query itself.
        try:
            return cast(TextLine, parse_line(f"1. {line}"))
        except PARSE_ERRORS:
            raise DataError("Invalid transliteration query.")


wildcard_matchers: dict = {
    "alternative": r"\[[^\]]*\|[^\]]*]",
    "any sign": r"\?",
    "any sign+": r"\*",
}

all_wildcards = '|'.join(
    [f'({wildcard_re})' for wildcard_re in wildcard_matchers.values()])


def classify(element: str):
    for name, regex in wildcard_matchers.items():
        if re.match(regex, element):
            return name
    return "text"


transliteration = '[a|]-na * qi2-bi2-ma ?-ma'


class TransliterationQueryElement:

    string: str
    type: str

    def __init__(self, string: str, type: str):
        self.type = type
        self.string = string

    @ property
    def re(self) -> re:
        ...


class TransliterationQueryText(TransliterationQueryElement):
    pass


class TransliterationQueryWildCard(TransliterationQueryElement):
    pass


class TransliterationQueryLine:

    elements: Sequence[TransliterationQueryElement]

    def __init__(self, transliteration: str):
        self.elements = self.create(transliteration)
        print(self.elements)

    def create(self, transliteration: str) -> Sequence[TransliterationQueryElement]:
        elements: Sequence[TransliterationQueryElement] = []
        for segment in [seg for seg in re.split(all_wildcards, transliteration) if seg]:
            segment_type = classify(segment)
            if segment_type != 'text':
                element = TransliterationQueryWildCard(
                    **{"string": segment, "type": segment_type})
            else:
                element = TransliterationQueryText(
                    **{"string": segment, "type": segment_type})
            elements.append(element)
        return elements

    @property
    def re(self) -> re:
        return


TransliterationQueryLine(**{"transliteration": transliteration})
