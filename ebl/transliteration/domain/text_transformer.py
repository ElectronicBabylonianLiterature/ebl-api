from lark.visitors import Transformer

from ebl.transliteration.domain.lark import tokens_to_value_tokens


class TextTransformer(Transformer):
    def text(self, children):
        return tokens_to_value_tokens(children)
