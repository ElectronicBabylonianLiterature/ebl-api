from typing import List, Tuple
from lark import Visitor, Tree, lexer

# ToDo:
# Remove. Use `legacy_atf_visitor` instead


class StripSigns(Visitor):
    def ebl_atf_text_line__legacy_uncertain_sign_prefix(self, tree: Tree) -> None:
        if (
            tree.data == "ebl_atf_text_line__legacy_uncertain_sign_prefix"
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
        input(f"line type data: {tree.data}, line type variable: {line_type}")
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

    def ebl_atf_text_line__single_line_number(self, tree: Tree) -> str:
        result = DepthFirstSearch().visit_topdown(tree, "")
        self.number += result
        return result


class GetWords(Visitor):
    def __init__(self):
        self.wordcounter = 0
        self.result = []
        self.alter_lem_line_at = []
        self.removal_open = False

    def ebl_atf_text_line__word(self, tree: Tree) -> None:
        assert tree.data == "ebl_atf_text_line__word"
        word = ""

        for child in tree.children:
            if child == "<<" and word == "":
                self.removal_open = True
            elif child == ">>" and self.removal_open:
                self.removal_open = False
                self.alter_lem_line_at.append(self.wordcounter)
            elif isinstance(child, lexer.Token):
                word += str(child)
            else:
                word += DepthFirstSearch().visit_topdown(child, "")


class GetLemmaValuesAndGuidewords(Visitor):
    result: List[List[Tuple[str, str, str]]] = []

    def oracc_atf_lem_line__lemma(self, tree: Tree) -> None:
        # ToDo:
        # Continue from here. Extract oracc_atf_lem_line parser,
        # use within ebl_atf parser or separately.
        lemmata: List[Tuple[str, str, str]] = []
        for child in tree.children:
            if child.data == "oracc_atf_lem_line__value_part":
                lemmata.append(self._get_oracc_atf_lem_line__value_part(child, tree))
        self.result.append(lemmata)

    def _get_oracc_atf_lem_line__value_part(
        self, child, tree: Tree
    ) -> Tuple[str, str, str]:
        lemma_value = DepthFirstSearch().visit_topdown(child, "")
        guide_word = self._get_child_data(1, tree) if len(tree.children) > 1 else ""
        pos_tag = self._get_child_data(2, tree) if len(tree.children) > 2 else ""
        return lemma_value, guide_word, pos_tag

    @staticmethod
    def _get_child_data(index: int, tree: Tree) -> str:
        return DepthFirstSearch().visit_topdown(tree.children[index], "")
