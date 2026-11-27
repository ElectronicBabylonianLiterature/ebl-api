import pytest

from ebl.signs.domain.mes_zl_kap2 import mes_zl_numbers, normalize_mes_zl_number
from ebl.transliteration.domain.sign import Sign, SignListRecord, SignName


@pytest.mark.parametrize(
    "number,expected",
    [
        ("579", "579"),
        (" 214' ", "214′"),
        ("214’", "214′"),
        ("214ʹ", "214′"),
        ("146''", "146′′"),
        ("214′", "214′"),
    ],
)
def test_normalize_mes_zl_number(number: str, expected: str) -> None:
    assert normalize_mes_zl_number(number) == expected


def test_mes_zl_numbers() -> None:
    sign = Sign(
        SignName("X"),
        lists=(
            SignListRecord("ABZ", "1"),
            SignListRecord("MZL", "2"),
            SignListRecord("MZL", "3'"),
        ),
    )
    assert mes_zl_numbers(sign) == ["2", "3'"]
