import attr

from typing import Sequence

from ebl.transliteration.domain.atf import VARIANT_SEPARATOR
from ebl.transliteration.domain.sign import Sign


@attr.s(auto_attribs=True, frozen=True)
class Standardization:
    deep: str
    shallow: str
    unicode: Sequence[int]

    @property
    def is_splittable(self) -> bool:
        return is_splittable(self.deep)

    def get_value(self, is_deep: bool):
        return self.deep if is_deep else self.shallow

    @classmethod
    def of_sign(cls, sign: Sign) -> "Standardization":
        shallow = cls.escape_standardization(sign)
        deep = sign.name if is_splittable(sign.name) else shallow
        return cls(deep, shallow, sign.unicode)

    @classmethod
    def of_string(cls, value: str) -> "Standardization":
        return cls(value, value, tuple(ord(char) for char in value))

    @staticmethod
    def escape_standardization(sign: Sign) -> str:
        return sign.standardization.replace(VARIANT_SEPARATOR, "\\u002F").replace(
            " ", "\\u0020"
        )


def is_splittable(grapheme: str) -> bool:
    return "." in grapheme and "(" not in grapheme and ")" not in grapheme


UNKNOWN = Standardization.of_string("X")
INVALID = Standardization.of_string("?")
