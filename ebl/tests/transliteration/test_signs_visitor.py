from typing import Sequence

import pytest

from ebl.transliteration.application.signs_visitor import SignsVisitor
from ebl.transliteration.domain.lark_parser import parse_line


@pytest.mark.parametrize(
    "text,expected",
    [
        ("ku gid₂ nu ši", ["KU", "BU", "ABZ075", "ABZ207a\\u002F207b\\u0020X"]),
        (
            "|(4×ZA)×KUR| |(AŠ&AŠ@180)×U| NU |GA₂#*+BAD!?| |GA₂#*.BAD!?|",
            ["ABZ531+588", "|(AŠ&AŠ@180)×U|", "ABZ075", "|GA₂+BAD|", "GA₂", "BAD"],
        ),
        (
            "ummu₃ |IGI.KU| mat₃ kunga",
            [
                "A",
                "ABZ168",
                "LAL",
                "ABZ207a\\u002F207b\\u0020X",
                "KU",
                "ABZ78",
                "HI",
                "ŠU₂",
                "3×AN",
            ],
        ),
        ("unknwn x X", ["?", "X", "X"]),
        (
            "1(AŠ) 1 2 10 20 30 256",
            ["ABZ001", "DIŠ", "2", "ABZ411", "ABZ411", "ABZ411", "30", "256"],
        ),
        ("| :", ["ABZ377n1"]),
        (
            ":/ku šu/|BI×IS|-ummu₃/|IGI.KU|/mat₃",
            ["ABZ377n1/KU", "ŠU/|BI×IS|", "|A.EDIN.LAL|/|IGI.KU|/ABZ081"],
        ),
        ("ku-[nu ši]", ["KU", "ABZ075", "ABZ207a\\u002F207b\\u0020X"]),
        ("< : ši>-ku", ["KU"]),
        ("ku-<<nu ši 1 |KU+KU| nu/ši nu(KU) x X ... : >>", ["KU"]),
        ("ku-<nu ši 1 |KU+KU| nu/ši nu(KU) x X ... : >", ["KU"]),
        ("ku-<(nu ši 1 |KU+KU| nu/ši nu(KU) x X ... : )>", ["KU"]),
        ("°nu : ši\\ku°", ["KU"]),
        ("ku-°|NU+NU|-1-nu-x-X-...-nu/ši\\ku°-ku", ["KU", "KU", "KU"]),
        ("<{ši>-ku} {ku-<ši}>", ["KU", "KU"]),
        ("<{+ši>-ku} {+ku-<ši}>", ["KU", "KU"]),
        ("<{{ši>-ku}} {{ku-<ši}}>", ["KU", "KU"]),
        ("{(ku)}", ["KU"]),
        ("%grc xX...ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω", []),
        ("%akkgrc xX...ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω", []),
        ("%suxgrc xX...ΑαΒβΓγΔδΕεΖζΗηΘθΙιΚκΛλΜμΝνΞξΟοΠπΡρΣσςΤτΥυΦφΧχΨψΩω", []),
        ("|BUL.U₁₈|", ["ABZ11", "ABZ78"]),
        ("|AMAR₂.AMAR₂|", ["AMAR₂", "AMAR₂"]),
    ],
)
def test_signs_visitor_string(
    text: str, expected: Sequence[str], sign_repository, signs
):
    for sign in signs:
        sign_repository.create(sign)

    visitor = SignsVisitor(sign_repository)
    parse_line(f"1. {text}").accept(visitor)
    assert visitor.result == expected


@pytest.mark.parametrize(
    "text,expected",
    [
        ("ku gid₂ nu ši", [74154, 73805, 74337, 74054]),
        (
            "|(4×ZA)×KUR| |(AŠ&AŠ@180)×U| NU |GA₂#*+BAD!?| |GA₂#*.BAD!?|",
            [
                74591,
                74499,
                74337,
                124,
                71,
                65,
                8322,
                43,
                66,
                65,
                68,
                124,
                124,
                71,
                65,
                8322,
                46,
                66,
                65,
                68,
                124,
            ],
        ),
    ],
)
def test_signs_visitor_unicode(
    text: str, expected: Sequence[str], sign_repository, signs
):
    for sign in signs:
        sign_repository.create(sign)

    visitor = SignsVisitor(sign_repository, False, True)
    parse_line(f"1. {text}").accept(visitor)
    assert visitor.result == expected
