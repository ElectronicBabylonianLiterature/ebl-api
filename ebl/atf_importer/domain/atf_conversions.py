from typing import List, Tuple
from lark import Visitor, Tree, lexer


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

    def __init__(self):
        self.result = []

    def oracc_atf_lem_line__lemma(self, tree: Tree) -> None:
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
