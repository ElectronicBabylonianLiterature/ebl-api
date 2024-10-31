import re
from typing import Optional, Sequence
from lark.visitors import Transformer, Tree, Token, v_args, Discard
from ebl.transliteration.domain.atf import _SUB_SCRIPT

# ToDo: Continue from here
# Make sure every transformer is implemented and works properly.
# Implement the rest, so the maximal possible number of transformations
# happens in the main (ebl) atf grammar.
# Write tests for all transformations!
# After this is done, clean up and get rid of preprocessing
# extept for `# note:` perhaps, if really needed.


class LegacyTransformer(Transformer):
    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        self.legacy_found = False
        self.current_path: Sequence[int] = []
        self.current_tree: Optional[Tree] = None
        self.break_at: Sequence[str] = []

    def clear(self) -> None:
        self.legacy_found = False
        self.current_path = []
        self.current_tree = None

    def transform(self, tree: Tree) -> Tree:
        result = super().transform(tree)
        return result if result else tree

    def _transform_children(self, children):
        for index, child in enumerate(children):
            self._enter_node(index)
            if self.is_classes_break_at(self.get_ancestors()):
                result = child
            elif isinstance(child, Tree):
                result = self._transform_tree(child)
            elif self.__visit_tokens__ and isinstance(child, Token):
                result = self._call_userfunc_token(child)
            else:
                result = child

            if result is not Discard:
                self._exit_node()
                yield result
            else:
                self._exit_node()

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
            ancestors.append(tree.children[parent_index].data)
            tree = tree.children[parent_index]
        return ancestors

    def is_classes_break_at(self, node_classes: Sequence[str]) -> bool:
        return not set(node_classes).isdisjoint(self.break_at)


class HalfBracketsTransformer(LegacyTransformer):
    # ToDo: Check if works

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.open = False

    def clear(self):
        super().clear()
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

    def _set_sub_index_from_accented(self, char: str) -> None:
        for pattern, sub_index in self.accented_index_patterns:
            if pattern.search(char):
                self._set_sub_index(sub_index)
                break

    def _set_sub_index(self, sub_index: str) -> None:
        sub_index_value = (
            Token("ebl_atf_text_line__SUB_INDEX", sub_index) if sub_index else None
        )
        self.sub_index = Tree(
            "ebl_atf_text_line__sub_index",
            [sub_index_value],
        )
