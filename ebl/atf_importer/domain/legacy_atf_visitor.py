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


class LegacyAtfVisitor(Visitor):
    # ToDo: Continue from here.
    # Move all atf preprocessing here
    # ?Try to convert to string and then parse?
    text_line_prefix = "ebl_atf_text_line"
    sign_rules = ["number", "reading", "logogram", "surrogate", "GRAPHEME_NAME"]
    legacy_damage_rules = ["_parts_pattern", "_parts_pattern_gloss"]
    legacy_joiner_rulers = ["LEGACY_ORACC_JOINER"]
    legacy_special_rulers = ["logogram"]

    def __init__(self):
        super().__init__()
        self.legacy_found = False
        self._set_rules(self.sign_rules, self.get_legacy_sign_transformer)
        self._set_rules(
            self.legacy_damage_rules,
            self.get_legacy_damage_transformer,
        )
        self._set_rules(
            self.legacy_joiner_rulers,
            self.get_legacy_joiner_transformer,
        )
        self._set_rules(
            self.legacy_special_rulers,
            self.get_legacy_special_transformer,
        )
        input("legacy visitor initiated")

    def _set_rules(
        self,
        rules: Sequence[str],
        method: Callable[[Tree], LegacyTransformer],
        prefix: Optional[str] = None,
    ) -> None:
        prefix = prefix if prefix else self.text_line_prefix
        for rule in rules:
            setattr(
                self,
                f"{prefix}__{rule}",
                self._wrap_legacy_found(method),
            )

    def _wrap_legacy_found(
        self, method: Callable[[Tree], LegacyTransformer]
    ) -> Callable[[Tree], Tree]:
        def _method(tree: Tree) -> Tree:
            # ToDo: Continue from here. Highest priority.
            # Transformations happen, but the original tree won't change.
            transformer = method(tree)
            tree = transformer.transform(tree)
            if transformer.legacy_found:
                self.legacy_found = True
            print("\n!!!! tree", tree)
            return tree

        return _method

    def get_legacy_sign_transformer(self, tree: Tree) -> LegacyTransformer:
        return AccentedIndexTransformer()

    def get_legacy_damage_transformer(self, tree: Tree) -> LegacyTransformer:
        return HalfBracketsTransformer()

    def get_legacy_joiner_transformer(self, tree: Tree) -> LegacyTransformer:
        return OraccJoinerTransformer()

    def get_legacy_special_transformer(self, tree: Tree) -> LegacyTransformer:
        return OraccSpecialTransformer()


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
    def ebl_atf_text_line__LEGACY_VALUE_CHARACTER_ACCENTED(self, char: str) -> str:
        print("!!!!!!!!!!!!!!!!!!!! LEGACY_VALUE_CHARACTER_ACCENTED")
        return self._transform_accented_vowel(char)

    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_LOGOGRAM_CHARACTER_ACCENTED(self, char: str) -> str:
        print("!!!!!!!!!!!!!!!!!!!! LEGACY_LOGOGRAM_CHARACTER_ACCENTED")
        return self._transform_accented_vowel(char)

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
