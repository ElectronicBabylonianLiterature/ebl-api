import re
from typing import Optional, Sequence, Callable
from lark.visitors import Visitor, Transformer, Tree, v_args

# ToDo: Continue from here
# Make sure every transformer is implemented and works properly.
# Implement the rest, so the maximal possible number of transformations
# happens in the main (ebl) atf grammar.
# Write tests for all transformations!
# After this is done, clean up and get rid of preprocessing
# extept for `# note:` perhaps, if really needed.


class HalfBracketsTransformer(Transformer):
    # ToDo: Check if works
    def __init__(self):
        super().__init__()
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


class OraccJoinerTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.legacy_found = False

    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_ORACC_JOINER(self, bracket: str) -> str:
        self.legacy_found = True
        return "-"


class OraccDividerTransformer(Transformer):
    def __init__(self):
        super().__init__()
        self.legacy_found = False

    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_ORACC_DIVIDER(self, bracket: str) -> str:
        self.legacy_found = True
        return "DIŠ"


class AccentedIndexTransformer(Transformer):
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
        self.legacy_found = False
        self.sub_index = None

    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_VALUE_CHARACTER_ACCENTED(self, char: str) -> str:
        return self._transform_accented_vowel(char)

    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_LOGOGRAM_CHARACTER_ACCENTED(self, char: str) -> str:
        return self._transform_accented_vowel(char)

    @v_args(inline=True)
    def ebl_atf_text_line__sub_index(self, char: Optional[str]) -> Optional[str]:
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


class LegacyAtfVisitor(Visitor):
    # ToDo: Continue from here.
    # Move all atf preprocessing here
    # ?Try to convert to string and then parse?
    text_line_prefix = "ebl_atf_text_line"
    sign_rules = ["number", "reading", "logogram", "surrogate", "GRAPHEME_NAME"]
    legacy_damage_rules = ["_parts_pattern", "_parts_pattern_gloss"]
    legacy_joiner_rulers = ["LEGACY_ORACC_JOINER"]
    legacy_divider_rulers = ["LEGACY_ORACC_DIVIDER"]

    def __init__(self):
        super().__init__()
        self.legacy_found = False
        self._set_rules(self.sign_rules, self.transform_legacy_sign)
        self._set_rules(
            self.legacy_damage_rules,
            self.transform_legacy_damage,
        )
        self._set_rules(
            self.legacy_joiner_rulers,
            self.transform_legacy_joiner,
        )
        self._set_rules(
            self.legacy_divider_rulers,
            self.transform_legacy_divider,
        )

    def _set_rules(
        self,
        rules: Sequence[str],
        method: Callable[[Tree], Transformer],
        prefix: Optional[str],
    ) -> None:
        prefix = prefix if prefix else self.prefix
        for rule in rules:
            setattr(
                self,
                f"{prefix}__{rule}",
                self._wrap_legacy_found(method),
            )

    def _wrap_legacy_found(self, method: Callable[[Tree], Transformer]) -> Callable[[Tree], None]:
        def _method(tree: Tree) -> None:
            transformer = method(tree)
            if transformer.legacy_found:
                self.legacy_found = True
        return _method

    def transform_legacy_sign(self, tree: Tree) -> None:
        return AccentedIndexTransformer(visit_tokens=True).transform(tree)

    def transform_legacy_damage(self, tree: Tree) -> None:
        return HalfBracketsTransformer().transform(tree)

    def transform_legacy_joiner(self, tree: Tree) -> None:
        return OraccJoinerTransformer().transform(tree)

    def transform_legacy_divider(self, tree: Tree) -> None:
        return OraccDividerTransformer().transform(tree)
