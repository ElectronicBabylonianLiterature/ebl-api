from ebl.corpus.domain.chapter import ChapterVisitor
from ebl.tests.factories.corpus import ManuscriptFactory, ManuscriptLineFactory


def test_base_visitor_visiting_a_manuscript_is_a_no_op() -> None:
    visitor = ChapterVisitor()

    visitor.visit(ManuscriptFactory.build())

    assert not vars(visitor)


def test_base_visitor_visiting_any_chapter_item_is_a_no_op() -> None:
    visitor = ChapterVisitor()

    visitor.visit(ManuscriptFactory.build())
    visitor.visit(ManuscriptLineFactory.build())

    assert not vars(visitor)
