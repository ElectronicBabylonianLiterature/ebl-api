import re
from typing import Optional, Sequence, Callable
from lark.visitors import Visitor, Transformer, Tree, Token, v_args

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


class HalfBracketsTransformer(LegacyTransformer):
    # ToDo: Check if works

    def __init__(self):
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
    patterns = ((re.compile("[áéíúÁÉÍÚ]"), "₂"), (re.compile("[àèìùÀÈÌÙ]"), "₃"))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.sub_index = None

    @v_args(inline=True)
    def ebl_atf_text_line__VALUE_CHARACTER(self, char: str) -> str:
        if char in self.replacement_chars.keys():
            print("!!!!!!!!!!!!!!!!!!!! LEGACY_VALUE_CHARACTER", char)
            return self._transform_accented_vowel(char)
        return char

    @v_args(inline=True)
    def ebl_atf_text_line__LOGOGRAM_CHARACTER(self, char: str) -> str:
        if char in self.replacement_chars.keys():
            print("!!!!!!!!!!!!!!!!!!!! LEGACY_LOGOGRAM_CHARACTER", char)
            return self._transform_accented_vowel(char)
        return char

    @v_args(inline=True)
    def ebl_atf_text_line__sub_index(self, char: Optional[str]) -> Optional[str]:
        print("!!!!!!!!!!!!!!!!!!!! ebl_atf_text_line__sub_index")
        return self.sub_index if self.sub_index and not char else char

    def _transform_accented_vowel(self, char: str) -> str:
        self._set_sub_index(char)
        self.legacy_found = True
        return self.replacement_chars[char]

    def _set_sub_index(self, char: str) -> None:
        for pattern, suffix in self.patterns:
            if pattern.search(char):
                self.sub_index = suffix
                break


accented_index_transformer = AccentedIndexTransformer()
half_brackets_transformer = HalfBracketsTransformer()
oracc_joiner_transformer = OraccJoinerTransformer()
oracc_special_transformer = OraccSpecialTransformer()


class LegacyAtfVisitor(Visitor):
    # ToDo: Continue from here.
    # Move all atf preprocessing here
    # ?Try to convert to string and then parse?
    text_line_prefix = "ebl_atf_text_line"
    tokens_to_visit = {
        "number": [accented_index_transformer],
        "reading": [accented_index_transformer],
        "logogram": [accented_index_transformer, oracc_special_transformer],
        "surrogate": [accented_index_transformer],
        "GRAPHEME_NAME": [accented_index_transformer],
        "_parts_pattern": [half_brackets_transformer],
        "_parts_pattern_gloss": [half_brackets_transformer],
        "LEGACY_ORACC_JOINER": [oracc_joiner_transformer],
    }

    def __init__(self):
        super().__init__()
        self.legacy_found = False
        for suffix, transformers in self.tokens_to_visit.items():
            self._set_rules(suffix, transformers)

        input("legacy visitor initiated")

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
            self._wrap_legacy_found(transformers),
        )

    def _wrap_legacy_found(
        self, transformers: Sequence[LegacyTransformer]
    ) -> Callable[[Tree], None]:
        def _method(tree: Tree) -> Tree:
            for transformer in transformers:
                # ToDo: Continue from here. Top Priority.
                # There is an error that likely has to do with
                # the token (`tree`) element being added children
                # disregarding the internal structure.
                # A possible approach for complex transformers (such as `AccentedIndexTransformer`)
                # might be saving the element as an attibute
                # of the `LegacyTransformer` class, then extracting it, e.g.:
                # transformer.transform(tree)
                # tree.children[0] = transformer.result
                # Make sure, however, that old results are not memorized:
                # Either initiate new instances or (better?) renew them on each run.
                tree.children[0] = transformer.transform(tree)
                if transformer.legacy_found:
                    self.legacy_found = True
            print("\nTransformed Tree:", tree.pretty())

        return _method
