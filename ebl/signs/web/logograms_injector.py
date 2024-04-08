from typing import Sequence

import re
import attr

from ebl.transliteration.application.sign_repository import SignRepository
from ebl.transliteration.domain.lark_parser import parse_text_line
from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.sign import Sign


def inject_logograms_unicode(
    signs: Sequence[Sign], word_id: str, sign_repository: SignRepository
) -> Sequence[Sign]:
    _signs = []
    for sign in signs:
        logograms = tuple(
            (
                attr.evolve(
                    logogram,
                    unicode=get_logogram_unicode(logogram.atf, sign_repository),
                )
                if word_id in logogram.word_id
                else logogram
            )
            for logogram in sign.logograms
        )
        _signs.append(sign.set_logograms(logograms))
    return _signs


def get_logogram_unicode(atf: str, sign_repository: SignRepository) -> str:
    unicode_list = []
    for atf_part in preprocess_logogram_atf(atf):
        signs_visitor = SignsVisitor(sign_repository, False, True)
        parse_text_line(f"1. {atf_part}").accept(signs_visitor)
        unicode_list.append("".join(chr(char) for char in signs_visitor.result_unicode))
    return ", ".join(unicode_list)


def preprocess_logogram_atf(atf: str) -> Sequence[str]:
    atf = re.sub(r"\(.*?\)", "", atf)
    if "→" in atf:
        atf = atf.split("→")[1]
    return [atf_part.strip("+ ") for atf_part in atf.split(",")]
