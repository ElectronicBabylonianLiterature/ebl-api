import re

import attr
import numpy as np
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
    sequence: np.array

    @staticmethod
    def of_signs(name, signs: str, vocabulary: Vocabulary) -> "NamedSequence":
        elements = vocabulary.encodeSequence(make_sequence(signs)).elements
        seq = np.array(elements, dtype=np.uint32)
        return NamedSequence(name, seq)

    @staticmethod
    def of_fragment(fragment_number, fragment_signs, vocabulary: Vocabulary) -> "NamedSequence":
        return NamedSequence.of_signs(fragment_number, fragment_signs, vocabulary)
