from enum import Enum, auto

from ebl.corpus.domain import text


class TextVisitor:
    class Order(Enum):
        PRE = auto()
        POST = auto()

    def __init__(self, order: "TextVisitor.Order"):
        self._order = order

    @property
    def is_post_order(self) -> bool:
        return self._order == TextVisitor.Order.POST

    @property
    def is_pre_order(self) -> bool:
        return self._order == TextVisitor.Order.PRE

    def visit_text(self, text: "text.Text") -> None:
        pass

    def visit_chapter(self, chapter: "text.Chapter") -> None:
        pass

    def visit_manuscript(self, manuscript: "text.Manuscript") -> None:
        pass

    def visit_line(self, line: "text.Line") -> None:
        pass

    def visit_manuscript_line(self, manuscript_line: "text.ManuscriptLine") -> None:
        pass
