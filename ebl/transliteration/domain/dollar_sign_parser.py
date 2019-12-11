from lark import Lark, Transformer
import attr
from typing import AnyStr
from ebl.transliteration.domain import atf

LINE_PARSER = Lark.open("ebl-atf-dollar-sign.lark", rel_to=__file__)
text = "$ at least hey"
tree = LINE_PARSER.parse(text)
print(tree.pretty())


class TreeToTokens(Transformer):
    def dollar_sign(self, dollar_sign):
        return DollarSign(dollar_sign)


@attr.s(auto_attribs=True, frozen=True)
class DollarSign:
    dollar_sign: AnyStr = attr.ib()

    @property
    def _sign(self) -> str:
        return atf.UNIDENTIFIED_SIGN
