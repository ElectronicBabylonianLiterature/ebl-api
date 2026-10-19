from ebl.atf_importer.domain.atf_indexing_visitor import IndexingVisitor
from ebl.atf_importer.domain.legacy_transformer_base import create_token, create_tree


def test_tokens_are_joined_by_a_single_space() -> None:
    tree = create_tree(
        "surface", [create_token("A", "obverse"), create_token("B", "!")]
    )

    assert IndexingVisitor()._tree_to_string(tree) == "obverse !"


def test_nested_trees_are_flattened() -> None:
    inner = create_tree("status", [create_token("B", "?")])
    tree = create_tree("surface", [create_token("A", "reverse"), inner])

    assert IndexingVisitor()._tree_to_string(tree) == "reverse ?"


def test_placeholder_children_are_skipped() -> None:
    inner = create_tree("status", [create_token("B", "a")])
    tree = create_tree("surface", [create_token("A", "edge"), None, inner])

    assert IndexingVisitor()._tree_to_string(tree) == "edge a"


def test_a_tree_of_only_placeholders_is_empty() -> None:
    assert IndexingVisitor()._tree_to_string(create_tree("surface", [None, None])) == ""


def test_reset_clears_the_cursor_and_the_column_counter() -> None:
    visitor = IndexingVisitor()
    visitor.column_counter = 7
    visitor.cursor = {"surface": "o", "column": "i", "line": "1"}

    visitor.reset()

    assert visitor.column_counter == 1
    assert visitor.cursor == {"surface": None, "column": None, "line": None}
