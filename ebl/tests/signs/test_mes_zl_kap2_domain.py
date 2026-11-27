from ebl.signs.domain.mes_zl_kap2 import mes_zl_numbers
from ebl.transliteration.domain.sign import Sign, SignListRecord, SignName


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
