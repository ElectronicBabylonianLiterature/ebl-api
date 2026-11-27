import attr

MES_ZL_LIST = "MZL"


@attr.s(auto_attribs=True, frozen=True)
class MesZlKap2Entry:
    number: str
    text: str


def mes_zl_number_variants(number: str) -> tuple[str, ...]:
    stripped = number.strip()
    return tuple(
        dict.fromkeys(
            [stripped, stripped.replace("'", "′"), stripped.replace("′", "'")]
        )
    )
