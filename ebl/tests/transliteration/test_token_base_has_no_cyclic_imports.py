import ast
from pathlib import Path
from types import ModuleType
from typing import List, Set

from ebl.transliteration.domain import enclosure_tokens, token_base, word_tokens

TOKEN_BASE_MODULE = "ebl.transliteration.domain.token_base"
TOKENS_MODULE = "ebl.transliteration.domain.tokens"

CONCRETE_TOKEN_MODULES = {
    "ebl.transliteration.domain.egyptian_metrical_feet_separator_token",
    "ebl.transliteration.domain.enclosure_tokens",
    "ebl.transliteration.domain.greek_tokens",
    "ebl.transliteration.domain.normalized_akkadian",
    "ebl.transliteration.domain.sign_tokens",
    "ebl.transliteration.domain.sign_token_base",
    "ebl.transliteration.domain.named_signs",
    TOKENS_MODULE,
    "ebl.transliteration.domain.unknown_sign_tokens",
    "ebl.transliteration.domain.word_tokens",
}


def _parse(module: ModuleType) -> ast.Module:
    return ast.parse(Path(str(module.__file__)).read_text(encoding="utf-8"))


def _imported_modules(module: ModuleType) -> Set[str]:
    tree = _parse(module)
    return {
        node.module
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module
    } | {
        alias.name
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }


def _references_type_checking(test: ast.expr) -> bool:
    return any(
        (isinstance(node, ast.Name) and node.id == "TYPE_CHECKING")
        or (isinstance(node, ast.Attribute) and node.attr == "TYPE_CHECKING")
        for node in ast.walk(test)
    )


def _type_checking_guards(module: ModuleType) -> List[ast.If]:
    return [
        node
        for node in ast.walk(_parse(module))
        if isinstance(node, ast.If) and _references_type_checking(node.test)
    ]


def test_token_base_does_not_import_any_concrete_token_module() -> None:
    assert _imported_modules(token_base) & CONCRETE_TOKEN_MODULES == set()


def test_token_base_has_no_type_checking_guard() -> None:
    assert _type_checking_guards(token_base) == []


def test_the_concrete_token_modules_depend_on_token_base() -> None:
    for module in (enclosure_tokens, word_tokens):
        assert _imported_modules(module) & {TOKEN_BASE_MODULE, TOKENS_MODULE}


def test_token_base_does_not_depend_back_on_them() -> None:
    for module in (enclosure_tokens, word_tokens):
        assert module.__name__ not in _imported_modules(token_base)
