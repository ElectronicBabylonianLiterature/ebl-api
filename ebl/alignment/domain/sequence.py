import re

import attr
from alignment.sequence import EncodedSequence, Sequence
from alignment.vocabulary import Vocabulary

from ebl.fragmentarium.domain.fragment import Fragment
from ebl.transliteration.domain.standardization import UNKNOWN


UNCLEAR_OR_UNKNOWN_SIGN = UNKNOWN.deep
LINE_BREAK = "#"


def replace_line_breaks(string: str) -> str:
    return string.replace("\n", f" {LINE_BREAK} ").strip()


def collapse_spaces(string: str) -> str:
    return re.sub(r"\s+", " ", string).strip()


def make_sequence(string: str) -> Sequence:
    return Sequence(
        collapse_spaces(
            replace_line_breaks(string).replace(UNCLEAR_OR_UNKNOWN_SIGN, " ")
        ).split(" ")
    )


@attr.s(auto_attribs=True, frozen=True)
class NamedSequence:
    name: str = attr.ib(converter=str)
    sequence: EncodedSequence

    @staticmethod
    def of_signs(name, signs: str, vocabulary: Vocabulary) -> "NamedSequence":
        return NamedSequence(name, vocabulary.encodeSequence(make_sequence(signs)))

    @staticmethod
    def of_fragment(fragment: Fragment, vocabulary: Vocabulary) -> "NamedSequence":
        return NamedSequence.of_signs(fragment.number, fragment.signs, vocabulary)
