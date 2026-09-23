from lark.tree import Tree

from ebl.atf_importer.domain.legacy_transformer_base import LegacyTransformer


def test_get_ancestors_without_a_current_tree_is_empty() -> None:
    transformer = LegacyTransformer()

    assert transformer.get_ancestors() == []


def test_get_ancestors_walks_the_current_path() -> None:
    leaf = Tree("leaf", [])
    middle = Tree("middle", [leaf])
    root = Tree("root", [middle])

    transformer = LegacyTransformer()
    transformer.current_tree = root
    transformer.current_path = [0, 0, 0]

    assert transformer.get_ancestors() == ["root", "middle", "leaf"]


def test_clear_resets_the_traversal_state() -> None:
    transformer = LegacyTransformer()
    transformer.legacy_found = True
    transformer.current_path = [1, 2]
    transformer.current_tree = Tree("root", [])

    transformer.clear()

    assert transformer.legacy_found is False
    assert transformer.current_path == []
    assert transformer.current_tree is None
