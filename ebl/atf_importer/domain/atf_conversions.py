import re
from typing import List, Tuple
from lark import Visitor, Tree, lexer


class ConvertLineDividers(Visitor):
    def atf_oracc_text_line__divider(self, tree: Tree) -> None:
        if tree.data == "atf_oracc_text_line__divider" and tree.children[0] == "*":
            tree.children[0] = "DIŠ"


class ConvertLineJoiner(Visitor):
    def atf_oracc_text_line__joiner(self, tree: Tree) -> None:
        if tree.data == "atf_oracc_text_line__joiner" and tree.children[0] == "--":
            tree.children[0] = "-"


class ConvertLegacyGrammarSigns(Visitor):
    replacement_chars: dict = {
        "á": "a",
        "é": "e",
        "í": "i",
        "ú": "u",
        "Á": "A",
        "É": "E",
        "Ì": "I",
        "Ú": "U",
    }

    def atf_oracc_text_line__logogram_name_part(self, tree: Tree) -> None:
        pattern = re.compile("[ÁÉÍÙ]")
        self.replace_characters(tree, pattern, "₂")

    def atf_oracc_text_line__value_name_part(self, tree: Tree) -> None:
        pattern = re.compile("[áéíú]")
        self.replace_characters(tree, pattern, "₃")

    def replace_character_in_child(
        self, tree: Tree, cnt: int, match: re.Match, default_suffix: str
    ) -> None:
        new_char = self.replacement_chars[match[0]]
        tree.children[cnt] = new_char
        if cnt + 1 < len(tree.children):
            tree.children[cnt + 1] += default_suffix
        else:
            tree.children[cnt] = f"{new_char}₂"

    def replace_characters(
        self, tree: Tree, pattern: re.Pattern, default_suffix: str
    ) -> None:
        for cnt, child in enumerate(tree.children):
            match = pattern.search(child)
            if match:
                self.replace_character_in_child(tree, cnt, match, default_suffix)


class StripSigns(Visitor):
    def atf_oracc_text_line__uncertain_sign(self, tree: Tree) -> None:
        if (
            tree.data == "atf_oracc_text_line__uncertain_sign"
            and tree.children[0] == "$"
        ):
            tree.children[0] = ""


class DepthFirstSearch(Visitor):
    def visit_topdown(self, tree: Tree, result: str) -> str:
        if not hasattr(tree, "data"):
            return result
        for child in tree.children:
            if isinstance(child, str):
                result = f"{result}{child}"
            else:
                result = self.visit_topdown(child, result)
        return result


class LineSerializer(Visitor):
    line: str = ""

    def process_line(self, tree: Tree, line_type: str) -> str:
        assert tree.data == line_type
        result = DepthFirstSearch().visit_topdown(tree, "")
        self.line += f" {result}"
        return result

    def text_line(self, tree: Tree) -> str:
        return self.process_line(tree, "text_line")

    def dollar_line(self, tree: Tree) -> str:
        return self.process_line(tree, "dollar_line")

    def control_line(self, tree: Tree) -> str:
        return self.process_line(tree, "control_line")


class GetLineNumber(Visitor):
    number: str = ""

    def atf_oracc_text_line__single_line_number(self, tree: Tree) -> str:
        result = DepthFirstSearch().visit_topdown(tree, "")
        self.number += result
        return result


class GetWords(Visitor):
    def __init__(self):
        self.wordcounter = 0
        self.result = []
        self.alter_lemline_at = []
        self.removal_open = False
        self.prefix = "oracc"

    def oracc_atf_text_line__word(self, tree):
        assert tree.data == "oracc_atf_text_line__word"
        word = ""

        for child in tree.children:
            if child == "<<" and word == "":
                self.removal_open = True
            elif child == ">>" and self.removal_open:
                self.removal_open = False
                self.alter_lemline_at.append(self.wordcounter)
            elif isinstance(child, lexer.Token):
                word += child
            else:
                word += DepthFirstSearch().visit_topdown(child, "")


class GetLemmaValuesAndGuidewords(Visitor):
    result: List[List[Tuple[str, str, str]]] = []

    def atf_oracc_lem_line__lemma(self, tree: Tree) -> None:
        lemmata: List[Tuple[str, str, str]] = []
        for child in tree.children:
            if child.data == "atf_oracc_lem_line__value_part":
                lemmata.append(self._get_atf_oracc_lem_line__value_part(child, tree))
        self.result.append(lemmata)

    def _get_atf_oracc_lem_line__value_part(
        self, child, tree: Tree
    ) -> Tuple[str, str, str]:
        lemma_value = DepthFirstSearch().visit_topdown(child, "")
        guide_word = self._get_child_data(1, tree) if len(tree.children) > 1 else ""
        pos_tag = self._get_child_data(2, tree) if len(tree.children) > 2 else ""
        return lemma_value, guide_word, pos_tag

    @staticmethod
    def _get_child_data(index: int, tree: Tree) -> str:
        return DepthFirstSearch().visit_topdown(tree.children[index], "")
