from lark import Lark, Transformer, v_args
import attr
from typing import AnyStr
from ebl.transliteration.domain import atf
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.tokens import Token


class TreeDollarSignToTokens(Transformer):
    @v_args(inline=True)
    def dollar_sign(self, prefix, content):
        return DollarLine(prefix, content)

    def loose(self, text):
        return Loose(text)


@attr.s(auto_attribs=True, frozen=True)
class DollarLine(Line):
    @classmethod
    def of(cls, prefix: str, content: Token):
        return cls(prefix, content)


@attr.s(auto_attribs=True, frozen=True)
class Loose(DollarLine):
    dollar_sign: AnyStr = attr.ib()


DOLLAR_SIGN_PARSER = Lark.open("ebl-atf-dollar-sign.lark", rel_to=__file__)
text = "$ wtf bro"
tree = DOLLAR_SIGN_PARSER.parse(text)
print(tree.pretty())
tokens = TreeDollarSignToTokens().transform(tree)
print(tokens)
