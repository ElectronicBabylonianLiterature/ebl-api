import attr

from ebl.transliteration.domain.sign import MES_ZL_LIST, Sign

PRIME = "′"
PRIME_LOOKALIKES = ("'", "’", "ʹ")


@attr.s(auto_attribs=True, frozen=True)
class MesZlKap2Entry:
    number: str
    text: str


def normalize_mes_zl_number(number: str) -> str:
    normalized = number.strip()
    for lookalike in PRIME_LOOKALIKES:
        normalized = normalized.replace(lookalike, PRIME)
    return normalized


def mes_zl_numbers(sign: Sign) -> list[str]:
    return [record.number for record in sign.lists if record.name == MES_ZL_LIST]
