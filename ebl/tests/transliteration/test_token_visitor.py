from ebl.transliteration.domain.tokens import TokenVisitor, ValueToken


def test_base_visitor_result_is_empty() -> None:
    assert TokenVisitor().result == []


def test_base_visitor_reset_leaves_an_empty_result() -> None:
    visitor = TokenVisitor()

    visitor.reset()

    assert visitor.result == []


def test_base_visitor_reset_is_idempotent_after_visiting() -> None:
    visitor = TokenVisitor()
    visitor.visit(ValueToken.of("kur"))

    visitor.reset()
    visitor.reset()

    assert visitor.result == []


def test_base_visitor_accumulates_no_state() -> None:
    visitor = TokenVisitor()

    visitor.visit(ValueToken.of("kur"))
    visitor.reset()

    assert not vars(visitor)
