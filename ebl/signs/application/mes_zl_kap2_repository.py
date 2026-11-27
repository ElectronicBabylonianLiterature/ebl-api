from abc import ABC, abstractmethod

import attr


@attr.s(auto_attribs=True, frozen=True)
class MesZlKap2Entry:
    """An entry of Borger, MesZL² Kapitel II, keyed by its MesZL number."""

    number: str
    text: str


def mes_zl_number_variants(number: str) -> list[str]:
    """MesZL numbers may be written with a prime (′) or an apostrophe (')."""
    stripped = number.strip()
    return list(
        dict.fromkeys(
            [stripped, stripped.replace("'", "′"), stripped.replace("′", "'")]
        )
    )


class MesZlKap2Repository(ABC):
    @abstractmethod
    def find(self, number: str) -> MesZlKap2Entry: ...
