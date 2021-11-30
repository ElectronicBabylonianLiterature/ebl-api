import re

import attr
from alignment.sequence import EncodedSequence, Sequence  # pyre-ignore[21]
from alignment.vocabulary import Vocabulary  # pyre-ignore[21]


UNCLEAR_OR_UNKNOWN_SIGN = "X"
LINE_BREAK = "#"


def replace_line_breaks(string: str) -> str:
    return string.replace("\n", f" {LINE_BREAK} ").strip()


def collapse_spaces(string: str) -> str:
    return re.sub(r"\s+", " ", string).strip()


def make_sequence(string: str) -> Sequence:  # pyre-ignore[11]
    return Sequence(
        collapse_spaces(
            replace_line_breaks(string).replace(UNCLEAR_OR_UNKNOWN_SIGN, " ")
        ).split(" ")
    )


@attr.s(auto_attribs=True, frozen=True)
class NamedSequence:
    name: str = attr.ib(converter=str)
    sequence: EncodedSequence  # pyre-ignore[11]

    @staticmethod
    def of_signs(
        name, signs: str, vocabulary: Vocabulary
    ) -> "NamedSequence":  # pyre-ignore[11]
        return NamedSequence(
            name, vocabulary.encodeSequence(make_sequence(signs))
        )  # pyre-ignore[19]
