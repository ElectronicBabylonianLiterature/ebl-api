import re
from typing import Optional, Sequence, Callable
from lark.visitors import Visitor, Transformer, Tree, Token, v_args
from ebl.transliteration.domain.atf import _SUB_SCRIPT

# ToDo: Continue from here
# Make sure every transformer is implemented and works properly.
# Implement the rest, so the maximal possible number of transformations
# happens in the main (ebl) atf grammar.
# Write tests for all transformations!
# After this is done, clean up and get rid of preprocessing
# extept for `# note:` perhaps, if really needed.


class LegacyTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.legacy_found = False

    def clear(self):
        self.legacy_found = False


class HalfBracketsTransformer(LegacyTransformer):
    # ToDo: Check if works

    def __init__(self):
        self.open = False

    def clear(self):
        self.legacy_found = False
        self.open = False

    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_OPEN_HALF_BRACKET(self, bracket: str) -> str:
        print("! bbbbbb", bracket)
        input()
        self.legacy_found = True
        self.open = True
        return ""

    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_CLOSE_HALF_BRACKET(self, bracket: str) -> str:
        print("! bbbbbb", bracket)
        input()
        self.legacy_found = True
        self.open = False
        return ""

    @v_args(inline=True)
    def ebl_atf_text_line__flags(self, flags: str):
        print("! bbbbbb", flags)
        input()
        return flags + "#" if self.open else flags


class OraccJoinerTransformer(LegacyTransformer):
    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_ORACC_JOINER(self, bracket: str) -> str:
        print("!!!!!!!!!!!!!!!!!!!! LEGACY_ORACC_JOINER")
        self.legacy_found = True
        return "-"


class OraccSpecialTransformer(LegacyTransformer):
    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_ORACC_DISH_DIVIDER(self, child: str) -> Tree:
        print("!!!!!!!!!!!!!!!!!!!! LEGACY_ORACC_DISH_DIVIDER")
        self.legacy_found = True
        return Tree(
            "ebl_atf_text_line__logogram_name_part",
            [Token("ebl_atf_text_line__LOGOGRAM_CHARACTER", char) for char in "DIŠ"],
        )


class AccentedIndexTransformer(LegacyTransformer):
    replacement_chars = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ú": "u",
        "à": "a",
        "è": "e",
        "ì": "i",
        "ù": "u",
        "Á": "A",
        "É": "E",
        "Í": "I",
        "Ú": "U",
        "À": "A",
        "È": "E",
        "Ì": "I",
        "Ù": "U",
    }
    accented_index_patterns = (
        (re.compile("[áéíúÁÉÍÚ]"), "₂"),
        (re.compile("[àèìùÀÈÌÙ]"), "₃"),
    )

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sub_index = None

    def clear(self):
        self.legacy_found = False
        self.sub_index = None

    @v_args(inline=True)
    def ebl_atf_text_line__VALUE_CHARACTER(self, char: str) -> str:
        if char in self.replacement_chars.keys():
            return self._transform_accented_vowel(char)
        return char

    @v_args(inline=True)
    def ebl_atf_text_line__LOGOGRAM_CHARACTER(self, char: str) -> str:
        if char in self.replacement_chars.keys():
            return self._transform_accented_vowel(char)
        return char

    @v_args(inline=True)
    def ebl_atf_text_line__sub_index(self, sub_index: Optional[str]) -> Optional[str]:
        if sub_index and sub_index[0] in _SUB_SCRIPT.keys():
            self.legacy_found = True
            self._set_sub_index("".join(_SUB_SCRIPT[digit] for digit in sub_index))
        return self.sub_index if self.sub_index else sub_index

    def _transform_accented_vowel(self, char: str) -> str:
        self._set_sub_index_from_accented(char)
        self.legacy_found = True
        return self.replacement_chars[char]

    def _set_sub_index_from_accented(self, char: str) -> None:
        for pattern, sub_index in self.accented_index_patterns:
            if pattern.search(char):
                self._set_sub_index(sub_index)
                break

    def _set_sub_index(self, sub_index: str) -> None:
        self.sub_index = Tree(
            "ebl_atf_text_line__sub_index",
            [Token("ebl_atf_text_line__SUB_INDEX", sub_index)],
        )


index_and_accented_transformer = (AccentedIndexTransformer(), "all_children")
half_brackets_transformer = (HalfBracketsTransformer(), "first_child")
oracc_joiner_transformer = (OraccJoinerTransformer(), "first_child")
oracc_special_transformer = (OraccSpecialTransformer(), "first_child")


class LegacyAtfVisitor(Visitor):
    text_line_prefix = "ebl_atf_text_line"
    tokens_to_visit = {
        "number": [index_and_accented_transformer],
        "reading": [index_and_accented_transformer],
        "logogram": [index_and_accented_transformer, oracc_special_transformer],
        "surrogate": [index_and_accented_transformer],
        "grapheme": [index_and_accented_transformer],
        "_parts_pattern": [half_brackets_transformer],
        "_parts_pattern_gloss": [half_brackets_transformer],
        "LEGACY_ORACC_JOINER": [oracc_joiner_transformer],
    }

    # ToDo: Fix nested `sign_index` within sign, as in `reading`.
    """
    ebl_atf_text_line__word
      ebl_atf_text_line__surrogate <-- ! Main parent
        ebl_atf_text_line__logogram_name 
          ebl_atf_text_line__logogram_name_part
            Š
            U
        ebl_atf_text_line__sub_index    ₂ <-- ! The expected subindex
        ebl_atf_text_line__modifiers
        ebl_atf_text_line__flags
        ebl_atf_text_line__surrogate_text
          ebl_atf_text_line__reading
            ebl_atf_text_line__value_name
              ebl_atf_text_line__value_name_part
                š
                u
                m
                m
                a
            ebl_atf_text_line__sub_index        ₂ <-- ! Problem here. Deeply nested second `sub_index`
            ebl_atf_text_line__modifiers
            ebl_atf_text_line__flags
            None
    """

    def __init__(self):
        super().__init__()
        self.legacy_found = False
        for suffix, transformers in self.tokens_to_visit.items():
            self._set_rules(suffix, transformers)
        input("LegacyAtfVisitor initiated")

    def _set_rules(
        self,
        suffix: str,
        transformers: Sequence[LegacyTransformer],
        prefix: Optional[str] = None,
    ) -> None:
        prefix = prefix if prefix else self.text_line_prefix
        setattr(
            self,
            f"{prefix}__{suffix}",
            self._wrap_transformers(transformers),
        )

    def _wrap_transformers(
        self, transformers: Sequence[LegacyTransformer]
    ) -> Callable[[Tree], None]:
        def _method(tree: Tree) -> Tree:
            for transformer, replace in transformers:
                self._transform(tree, transformer, replace)

        return _method

    def _transform(self, tree: Tree, transformer: LegacyTransformer, replace: str):
        transformer.clear()
        transformed = transformer.transform(tree)
        if transformer.legacy_found:
            self.legacy_found = True
            if replace == "first_child":
                tree.children[0] = transformed.children[0]
            elif replace == "all_children":
                tree.children = transformed.children
