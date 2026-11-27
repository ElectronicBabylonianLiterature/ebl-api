import attr

from ebl.transliteration.domain.sign import MES_ZL_LIST, Sign


@attr.s(auto_attribs=True, frozen=True)
class MesZlKap2Entry:
    number: str
    text: str


def mes_zl_numbers(sign: Sign) -> list[str]:
    return [record.number for record in sign.lists if record.name == MES_ZL_LIST]
