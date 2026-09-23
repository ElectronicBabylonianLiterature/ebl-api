import logging

from ebl.atf_importer.application.logger import Logger
from ebl.atf_importer.domain.atf_indexing_visitor import IndexingVisitor
from ebl.atf_importer.domain.legacy_atf_transformers import LegacyAlephTransformer
from ebl.atf_importer.domain.legacy_transformer_base import create_token, create_tree


def test_set_level_reaches_the_underlying_logger() -> None:
    logger = Logger()

    logger.setLevel(logging.CRITICAL)

    assert logger.logger.level == logging.CRITICAL


def test_exception_is_recorded_under_its_key(tmp_path) -> None:
    logger = Logger(tmp_path)

    logger.exception("boom", "error_lines")

    assert logger.data["error_lines"] == ["boom"]


def test_exception_is_prefixed_with_the_current_filepath(tmp_path) -> None:
    logger = Logger(tmp_path)
    logger.filepath = "tablet.atf"

    logger.exception("boom", "error_lines")

    assert logger.data["error_lines"] == ["tablet.atf: boom"]


def test_exception_without_a_key_records_nothing(tmp_path) -> None:
    logger = Logger(tmp_path)

    logger.exception("boom")

    assert all(entries == [] for entries in logger.data.values())


def test_legacy_columns_are_numbered_with_lowercase_roman_numerals() -> None:
    visitor = IndexingVisitor()
    tree = create_tree("legacy_column", [])

    columns = []
    for _ in range(4):
        visitor.ebl_atf_at_line__legacy_column(tree)
        columns.append(visitor.cursor["column"])

    assert columns == ["i", "ii", "iii", "iv"]


def test_legacy_column_returns_the_tree_it_was_given() -> None:
    visitor = IndexingVisitor()
    tree = create_tree("legacy_column", [])

    assert visitor.ebl_atf_at_line__legacy_column(tree) is tree


def test_resetting_restarts_the_column_numbering() -> None:
    visitor = IndexingVisitor()
    tree = create_tree("legacy_column", [])
    visitor.ebl_atf_at_line__legacy_column(tree)
    visitor.ebl_atf_at_line__legacy_column(tree)

    visitor.reset()
    visitor.ebl_atf_at_line__legacy_column(tree)

    assert visitor.cursor["column"] == "i"


def test_an_apostrophe_becomes_an_aleph() -> None:
    transformer = LegacyAlephTransformer()

    result = transformer.ebl_atf_text_line__VALUE_CHARACTER(create_token("V", "'"))

    assert str(result) == "ʾ"
    assert transformer.legacy_found is True


def test_any_other_value_character_is_left_alone() -> None:
    transformer = LegacyAlephTransformer()
    token = create_token("V", "a")

    assert transformer.ebl_atf_text_line__VALUE_CHARACTER(token) is token
    assert transformer.legacy_found is False
