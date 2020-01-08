from lark import Lark, Transformer, v_args
import attr

from ebl.transliteration.domain import atf
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.tokens import Token, ValueToken


class TreeDollarSignToTokens(Transformer):
    @v_args(inline=True)
    def loose(self, content):
        return Loose("$", (ValueToken(str(content)),), content.value[1:-1])

    @v_args(inline=True)
    def images(self, number, lower_case_letter, text):
        return Image(number, lower_case_letter, text)

    def strict(self, content):
        return Strict(content=content)

    def rulings(self, ruling):
        return Ruling(number=ruling)


@attr.s(auto_attribs=True, frozen=True)
class DollarLine(Line):
    pass


@attr.s(auto_attribs=True, frozen=True)
class Loose(DollarLine):
    text: str = ""


@attr.s(auto_attribs=True, frozen=True)
class Image(DollarLine):
    number: int = attr.ib(kw_only=True)
    letter: str = attr.ib(kw_only=True)
    text: str = attr.ib(kw_only=True)


@attr.s(auto_attribs=True, frozen=True)
class Strict(DollarLine):
    content: [] = attr.ib(kw_only=True)


@attr.s(auto_attribs=True, frozen=True)
class Ruling(DollarLine):
    ENUM = {"single", "double", "triple"}
    number: str = attr.ib() if attr.ib() in ENUM else ""


if __name__ == "__main__":
    DOLLAR_SIGN_PARSER = Lark.open("ebl_atf_dollar_sign.lark", rel_to=__file__)
    text = "$ (end of side)"
    tree = DOLLAR_SIGN_PARSER.parse(text)
    print(tree.pretty())
    tokens = TreeDollarSignToTokens().transform(tree)
    print(tokens)
