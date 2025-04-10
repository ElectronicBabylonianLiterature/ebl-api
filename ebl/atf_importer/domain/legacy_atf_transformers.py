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
        result = self._remove_discard_nodes(super().transform(tree))
        return result if result else tree

    def _transform_children(self, children: Sequence[Tree]):
        index_correction = 0
        for index, child in enumerate(children):
            self._enter_node(index - index_correction)
            result = self._get_child_result(child)
            self._exit_node()
            if result is not Discard:
                yield result

    def _get_child_result(self, child: Tree) -> Tree:
        if self.is_classes_break_at(self.get_ancestors()):
            return child
        elif isinstance(child, Tree):
            return self._transform_tree(child)
        elif self.__visit_tokens__ and isinstance(child, Token):
            return self._call_userfunc_token(child)
        else:
            return child

    def _enter_node(self, index: int = 0) -> None:
        self.current_path.append(index)

    def _exit_node(self) -> None:
        if self.current_path:
            self.current_path.pop()

    def get_ancestors(self) -> Sequence:
        if not self.current_tree:
            return []
        tree = self.current_tree
        ancestors = [tree.data]
        for parent_index in self.current_path[:-1]:
            ancestor = tree.children[parent_index]
            ancestors.append(ancestor.data)
            tree = tree.children[parent_index]
        return ancestors

    def is_classes_break_at(self, node_classes: Sequence[str]) -> bool:
        return not set(node_classes).isdisjoint(self.break_at)

    def _remove_discard_nodes(self, tree: Tree) -> Tree:
        if isinstance(tree, Tree):
            tree.children = [
                self._remove_discard_nodes(child)
                for child in tree.children
                if child is not Discard
            ]
        return tree

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


class LegacyStateTransformer(LegacyTransformer):
    prefix = "ebl_atf_dollar_line"

    @v_args(inline=True)
    def ebl_atf_dollar_line__legacy_broken_state(self) -> Tree:
        self.legacy_found = True
        return self.to_tree(
            "state_extent",
            [
                self.to_token("EXTENT", "rest of"),
                self.to_token("SCOPE", "side"),
                self.to_token("STATE", "broken"),
                None,
            ],
        )


class LegacyRulingTransformer(LegacyTransformer):
    prefix = "ebl_atf_dollar_line"

    @v_args(inline=True)
    def ebl_atf_dollar_line__legacy_single_ruling(
        self, status: Optional[Token] = None
    ) -> Tree:
        self.legacy_found = True
        if status:
            status = self.to_token("DOLLAR_STATUS", str(status))
        return self.to_tree(
            "ruling", [self.to_token("RULING_NUMBER", "single"), status]
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

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.reset()

    def reset(self):
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
    prefix = ""

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.reset()

    def reset(self) -> None:
        self.language: Optional[Token] = None
        self.start: Optional[str] = None
        self.extent: Sequence[Tree] = []
        self.translation: List[str] = []

    @property
    def translation_c_line(self) -> Tree:
        return self.to_tree(
            "!translation_line",
            [
                self.language,
                self._translation_extent,
                self._translation_string_part,
            ],
        )

    @property
    def _translation_extent(self) -> Optional[Tree]:
        return (
            self.to_tree("ebl_atf_translation_line__translation_extent", self.extent)
            if self.extent
            else None
        )

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
        self, language: Optional[Token]
    ) -> None:
        self.reset()
        self.legacy_found = True
        self.language = language
        return

    @v_args(inline=True)
    def ebl_atf_translation_line__labels_start(self, labels: Tree) -> None:
        self.reset()
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
    ) -> Tree:
        self.legacy_found = True
        self.translation.append("".join([str(child) for child in text.children]))
        return self.translation_c_line

    def ebl_atf_translation_line__legacy_translation_block_label_text_line(
        self, line: Sequence[Tree]
    ) -> Tree:
        return line[1]
