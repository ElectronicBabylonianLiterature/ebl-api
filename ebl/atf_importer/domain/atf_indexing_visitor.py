import roman
from lark.visitors import Visitor, Tree

surface_mapping = {
    "obverse": "o",
    "reverse": "r",
    "bottom": "b.e.",
    "edge": "e.",
    "left": "l.e.",
    "right": "r.e.",
    "top": "t.e.",
}


class IndexingVisitor(Visitor):
    def __init__(self):
        super().__init__()
        self._reset()

    def _reset(self) -> None:
        self.column_counter = 1
        self.cursor = {"surface": None, "column": None, "line": None}

    def ebl_atf_at_line__surface_with_status(self, tree: Tree) -> Tree:
        surface = surface_mapping[str(tree.children[0])] + "".join(
            str(child) for child in tree.children[1].children
        )
        self.cursor["surface"] = surface
        return tree

    def ebl_atf_at_line__legacy_column(self, tree: Tree) -> Tree:
        self.cursor["column"] = roman.toRoman(self.column_counter).lower()
        self.column_counter += 1
        return tree

    def ebl_atf_at_line__column(self, tree: Tree) -> Tree:
        self.cursor["column"] = roman.toRoman(str(tree.children[0])).lower() + "".join(
            str(child) for child in tree.children[1].children
        )
        return tree

    def text_line(self, tree: Tree) -> Tree:
        line_number = "".join(
            str(child) for child in tree.children[0].children if child
        )
        self.cursor["line"] = line_number
        return tree

    @property
    def cursor_index(self) -> str:
        return " ".join(
            [
                str(self.cursor[key])
                for key in ["surface", "column", "line"]
                if self.cursor[key]
            ]
        )
