import re
import numpy as np

import attr
from alignment.sequence import Sequence

from ebl.transliteration.domain.standardization import UNKNOWN

UNCLEAR_OR_UNKNOWN_SIGN = UNKNOWN.deep
LINE_BREAK = "#"

def has_clear_signs(signs: str) -> bool:
    return not re.fullmatch(r"[X\\n\s]*", signs)

def replace_line_breaks(string: str) -> str:
    return string.replace("\n", f" {LINE_BREAK} ").strip()


def collapse_spaces(string: str) -> str:
    return re.sub(r"\s+", " ", string).strip()


def make_sequence(string: str) -> Sequence:
    return collapse_spaces(
            replace_line_breaks(string).replace(UNCLEAR_OR_UNKNOWN_SIGN, " ")
        ).split(" ")


@attr.s(auto_attribs=True, frozen=True)
class NamedEncoding:
    name: str = attr.ib(converter=str)
    sequence: np.array



class SignsVocabulary:
    _irregular_encodings_list = ['#' , 'ABZ143/ABZ126/ABZ214', '', 'ABZ342/ABZ5', 'KISIM₅×GIR₂', 'ABZ308/ABZ322', 'iš', 'ABZ57/ABZ205', 'LAGAB×HAL', 'ABZ461/ABZ459a/ABZ457', 'ABZ374/ABZ73', 'ABZ481/ABZ532', 'NUN&NUN', '4', '9', 'ABZ115/ABZ15', 'GIDRU', 'ABZ233/ABZ313', 'HI×BAD', 'QA', 'ABZ69/ABZ74', 'ABZ232/ABZ231', '150', 'NAB', 'ABZ537/ABZ536', 'ABZ457/ABZ461', '   ', '27', '24', 'ABZ55/ABZ7']
    encoding = {}
    decoding = {}

    def __init__(self, signs):
        self.encoding = {sign: i for i, sign in enumerate(self._irregular_encodings_list)}
        self.decoding = {i: sign for i, sign in enumerate(self._irregular_encodings_list)}

        self._build_alignment_encoding(signs)

    def _build_alignment_encoding(self, signs):
        encoding = {}
        decoding = {}
        for i, sign in enumerate(sorted(signs)):
            i = i + len(self.encoding.items())
            encoding[sign.standardization] = i
            decoding[i] = sign.standardization
        self.encoding = self.encoding | encoding
        self.decoding = decoding | self.decoding

    def _encodeSequence(self, sequence):
        encoded = []
        for elem in sequence:
            enc = self.encoding.get(elem, None)
            if enc is None:
                raise ValueError("Sign in sequence not in encoding: " + elem)
            else:
                encoded.append(enc)
        return np.array(encoded, dtype=np.uint32)


    def encodeSequence(self, sequence):
        return self._encodeSequence(make_sequence(sequence))


    def encodeToNamedSeq(self, name, sequence):
        return NamedEncoding(name, self.encodeSequence(sequence))
    def decodeSequence(self, sequence):
        return [self.decoding[element] for element in sequence]