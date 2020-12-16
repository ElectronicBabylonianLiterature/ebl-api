from ebl.corpus.domain.chapter import Chapter, Line, ManuscriptLine
from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.text import Text, VisitText


class TextVisitor(VisitText):
    def visit_text(self, text: Text) -> None:
        pass

    def visit_chapter(self, chapter: Chapter) -> None:
        pass

    def visit_manuscript(self, manuscript: Manuscript) -> None:
        pass

    def visit_line(self, line: Line) -> None:
        pass

    def visit_manuscript_line(self, manuscript_line: ManuscriptLine) -> None:
        pass
