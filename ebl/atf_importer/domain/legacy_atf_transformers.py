import re
from typing import Optional, List, Sequence, Union, Type
from lark.visitors import Transformer, Tree, Token, v_args, Discard
from ebl.transliteration.domain.atf import _SUB_SCRIPT
from ebl.transliteration.domain.common_transformer import CommonTransformer

# ToDo: Continue from here
# Make sure every transformer is implemented and works properly.
# Implement the rest, so the maximal possible number of transformations
# happens in the main (ebl) atf grammar.
# Write tests for all transformations!
# After this is done, clean up and get rid of preprocessing
# extept for `# note:` perhaps, if really needed.


class LegacyTransformer(Transformer):
    prefix = "ebl_atf_text_line"

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.legacy_found = False
        self.current_path: List[int] = []
        self.current_tree: Optional[Tree] = None
        self.break_at: Sequence[str] = []

    def clear(self) -> None:
        self.legacy_found = False
        self.current_path = []
        self.current_tree = None

    def transform(self, tree: Tree) -> Tree:
        result = super().transform(tree)
        return result if result else tree

    def to_token(self, name: str, string: Optional[str]) -> Token:
        return (
            Token(f"{self.prefix}__{name}", string)
            if self.prefix
            else Token(name, string)
        )

    def to_tree(
        self, name: str, children: Sequence[Optional[Union[Tree, Token]]]
    ) -> Tree:
        return (
            Tree(f"{self.prefix}__{name}", children)
            if self.prefix
            else Tree(name, children)
        )


class HalfBracketsTransformer(LegacyTransformer):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.open = False

    def clear(self):
        super().clear()
        self.open = False

    @v_args(inline=True)
    def ebl_atf_text_line__open_legacy_damage(self, bracket: str) -> Type[Discard]:
        self.legacy_found = True
        self.open = True
        return Discard

    @v_args(inline=True)
    def ebl_atf_text_line__close_legacy_damage(self, bracket: str) -> Type[Discard]:
        self.legacy_found = True
        self.open = False
        return Discard

    @v_args(inline=True)
    def ebl_atf_text_line__flags(self, *flags) -> Tree:
        damage_flag = self.to_token("DAMAGE", "#") if self.open else None
        _flags = [flag for flag in [*flags, damage_flag] if flag]
        return self.to_tree("flags", _flags if _flags else [])


class OraccJoinerTransformer(LegacyTransformer):
    @v_args(inline=True)
    def ebl_atf_text_line__joiner(self, joiner: Token) -> Tree:
        if joiner.type == "ebl_atf_text_line__LEGACY_ORACC_JOINER":  # type: ignore
            self.legacy_found = True
            return self.to_tree("joiner", [Token("MINUS", "-")])
        return self.to_tree("joiner", [joiner])


class OraccSpecialTransformer(LegacyTransformer):
    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_ORACC_DISH_DIVIDER(self, child: str) -> Tree:
        self.legacy_found = True
        return self.to_tree(
            "logogram_name_part",
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
        self.break_at = ["ebl_atf_text_line__surrogate_text"]

    def clear(self):
        super().clear()
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
        elif not self.sub_index:
            self._set_sub_index(sub_index)
        return self.sub_index

    def _transform_accented_vowel(self, char: str) -> str:
        self._set_sub_index_from_accented(char)
        self.legacy_found = True
        return self.replacement_chars[char]

    def _set_sub_index_from_accented(self, char: Optional[str]) -> None:
        for pattern, sub_index in self.accented_index_patterns:
            if pattern.search(char):
                self._set_sub_index(sub_index)
                break

    def _set_sub_index(self, sub_index: Optional[str]) -> None:
        sub_index_value = self.to_token("SUB_INDEX", sub_index) if sub_index else None
        self.sub_index = self.to_tree(
            "sub_index",
            [sub_index_value],
        )


class UncertainSignTransformer(LegacyTransformer):
    @v_args(inline=True)
    def ebl_atf_text_line__legacy_uncertain_sign(
        self, prefix: Tree, sign: Tree
    ) -> Tree:
        self.legacy_found = True
        return sign


class LegacyModifierPrefixTransformer(LegacyTransformer):
    @v_args(inline=True)
    def ebl_atf_text_line__LEGACY_MODIFIER_PREFIX(self, prefix: Token) -> Token:
        self.legacy_found = True
        return self.to_token("MODIFIER_PREFIX", "@")


class LegacyPrimeTransformer(LegacyTransformer):
    prefix = "ebl_atf_text_line__ebl_atf_common"

    @v_args(inline=True)
    def ebl_atf_text_line__ebl_atf_common__LEGACY_PRIME(self, prime: Token) -> Token:
        self.legacy_found = True
        return self.to_token("PRIME", "'")


class LegacyAlephTransformer(LegacyTransformer):
    @v_args(inline=True)
    def ebl_atf_text_line__VALUE_CHARACTER(self, token: Token) -> Token:
        if str(token) == "'":
            self.legacy_found = True
            token = self.to_token("VALUE_CHARACTER", "ʾ")
        return token


class LegacyColumnTransformer(LegacyTransformer):
    prefix = ""

    # ToDo:
    # Add indexing to detect the beginnging of the text.
    # Then reset the column number when a new text begins.

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.column_number = 1

    @v_args(inline=True)
    def ebl_atf_at_line__legacy_column(self) -> Tree:
        self.legacy_found = True
        column_number = self.column_number
        self.column_number += 1
        return self.to_tree(
            "ebl_atf_at_line__column",
            [
                self.to_token("ebl_atf_at_line__INT", str(column_number)),
                self.to_tree("ebl_atf_at_line__status", []),
            ],
        )


class LegacyTranslationBlockTransformer(LegacyTransformer):
    #
    # ToDo: Continue from here.
    # Write an injector that detects the correct line.
    # This can be implemented using the lables & line number in `self.start`.
    # It would make sense to trace labels & line numbers within the `LegacyTransformer` or the visitor:
    # Write methods for `...__labels` and `...__ebl_atf_common__single_line_number` to capture the data and save it within the class.
    # Then, text lines can be indexed accordingly.
    # The main issue to consider is detecting the end of the translation block to inject the translation line at this point.
    # The most obvious option would be detecting the beginning of each block and then the the beginning of a new text
    # or end of all texts.
    #
    # Ensure that this works, then clean up.

    prefix = ""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self._reset()

    def _reset(self) -> None:
        self.language: Optional[Token] = None
        self.start: Optional[str] = None
        self.extent: Optional[Sequence[Tree]] = None
        self.translation: Sequence[str] = []

    @property
    def translation_c_line(self) -> Sequence[Union[Tree, Token]]:
        return self.to_tree(
            "translation_line",
            [
                self.language,
                self._translation_extent,
                self._translation_string_part,
            ],
        )

    @property
    def _translation_extent(self) -> Tree:
        return self.to_tree("ebl_atf_translation_line__translation_extent", self.extent)

    @property
    def _translation_string_part(self) -> Tree:
        line_token = self.to_token(
            "__ANON_26", " ".join(self.translation).replace(r"/[\s]+/", " ")
        )
        note_text = self.to_tree(
            "ebl_atf_translation_line__ebl_atf_note_line__note_text", [line_token]
        )
        return self.to_tree(
            "ebl_atf_translation_line__ebl_atf_note_line__string_part", [note_text]
        )

    @v_args(inline=True)
    def ebl_atf_translation_line__legacy_translation_block_at_line(
        self, language: str
    ) -> None:
        self._reset()
        self.legacy_found = True
        self.language = language
        return

    @v_args(inline=True)
    def ebl_atf_translation_line__labels_start(self, labels: Tree) -> None:
        self.legacy_found = True
        self.start = self._labels_to_string(labels)
        return

    @v_args(inline=True)
    def ebl_atf_translation_line__labels_extent(self, labels: Tree) -> None:
        self.legacy_found = True
        self.extent = labels.children
        return

    def _labels_to_string(self, labels: Tree) -> str:
        labels, line_number = CommonTransformer().transform(labels).children
        return (
            " ".join(label.to_value() for label in labels)
            + " "
            + str(line_number.number)
        )

    @v_args(inline=True)
    def ebl_atf_translation_line__legacy_translation_block_line(
        self, text: Tree
    ) -> None:
        self.legacy_found = True
        self.translation.append(str(text.children[0]))
        return self.translation_c_line
