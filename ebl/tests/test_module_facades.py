import ast
import importlib
from pathlib import Path
from typing import Iterator, List, Set, Tuple

import pytest

FACADE_SOURCES = {
    "ebl.corpus.web.chapter_schemas": ("ebl.corpus.web.chapter_manuscript_schemas",),
    "ebl.fragmentarium.retrieve_annotations": (
        "ebl.fragmentarium.retrieve_annotations_helpers",
    ),
    "ebl.signs.infrastructure.mongo_sign_repository": (
        "ebl.signs.infrastructure.sign_schemas",
        "ebl.signs.infrastructure.sign_unicode_lookup",
    ),
    "ebl.tests.factories.fragment": (
        "ebl.tests.factories.first_text_line",
        "ebl.tests.factories.fragment_metadata_factories",
        "ebl.tests.factories.fragment_text_words",
        "ebl.tests.factories.lemmatized_fragment_text",
        "ebl.tests.factories.transliterated_fragment_lines",
        "ebl.tests.factories.transliterated_fragment_text",
    ),
    "ebl.transliteration.domain.enclosure_visitor": (
        "ebl.transliteration.domain.enclosure_state",
        "ebl.transliteration.domain.enclosure_updater",
    ),
    "ebl.transliteration.domain.sign_tokens": (
        "ebl.transliteration.domain.named_signs",
        "ebl.transliteration.domain.sign_token_base",
    ),
    "ebl.transliteration.domain.tokens": ("ebl.transliteration.domain.token_base",),
}

FACADE_MODULES = sorted(FACADE_SOURCES)


def _exports(module_name: str) -> List[str]:
    return list(vars(importlib.import_module(module_name))["__all__"])


def _parse(module_name: str) -> Tuple[ast.Module, List[str]]:
    module = importlib.import_module(module_name)
    source = Path(str(module.__file__)).read_text(encoding="utf8")
    return ast.parse(source), _exports(module_name)


def _is_public(name: str) -> bool:
    return not name.startswith("_")


def _assigned_names(node: ast.Assign) -> Iterator[str]:
    for target in node.targets:
        if isinstance(target, ast.Name):
            yield target.id


def _defined_names(tree: ast.Module) -> Set[str]:
    names = set()
    for node in tree.body:
        if isinstance(node, (ast.ClassDef, ast.FunctionDef)) and _is_public(node.name):
            names.add(node.name)
        elif isinstance(node, ast.Assign):
            names.update(
                name
                for name in _assigned_names(node)
                if _is_public(name) and name != "__all__"
            )
        elif isinstance(node, ast.AnnAssign):
            target = node.target
            if isinstance(target, ast.Name) and _is_public(target.id):
                names.add(target.id)
    return names


@pytest.mark.parametrize("module_name", FACADE_MODULES)
def test_facade_exports_every_name_it_defines(module_name: str) -> None:
    tree, exported = _parse(module_name)

    missing = sorted(_defined_names(tree) - set(exported))

    assert missing == [], (
        f"{module_name} defines public names absent from __all__: {missing}. "
        "A split module's facade must cover what it defines, not only what it "
        "re-exports."
    )


@pytest.mark.parametrize("module_name", FACADE_MODULES)
def test_facade_exports_are_all_importable(module_name: str) -> None:
    module = importlib.import_module(module_name)

    missing = sorted(
        name for name in _exports(module_name) if not hasattr(module, name)
    )

    assert missing == [], f"{module_name}.__all__ names nothing it provides: {missing}"


@pytest.mark.parametrize("module_name", FACADE_MODULES)
def test_facade_exports_are_sorted_and_unique(module_name: str) -> None:
    exported = _exports(module_name)

    assert exported == sorted(set(exported)), (
        f"{module_name}.__all__ must be sorted and free of duplicates, "
        "so a second assignment cannot silently overwrite the first."
    )


def _names_taken_from(tree: ast.Module, sources: Tuple[str, ...]) -> Set[str]:
    names: Set[str] = set()
    for node in tree.body:
        if isinstance(node, ast.ImportFrom) and node.module in sources:
            names.update(
                alias.asname or alias.name
                for alias in node.names
                if _is_public(alias.asname or alias.name)
            )
    return names


@pytest.mark.parametrize("module_name", FACADE_MODULES)
def test_facade_exports_every_name_it_re_exports(module_name: str) -> None:
    tree, exported = _parse(module_name)

    taken = _names_taken_from(tree, FACADE_SOURCES[module_name])
    missing = sorted(taken - set(exported))

    assert missing == [], (
        f"{module_name} takes public names from the modules it was split into "
        f"but does not export them: {missing}. `from {module_name} import *` "
        "would silently lose them, which is the regression this facade exists "
        "to prevent."
    )
