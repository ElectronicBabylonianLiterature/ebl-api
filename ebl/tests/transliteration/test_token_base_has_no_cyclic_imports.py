import ast
from pathlib import Path
from typing import Set

from ebl.transliteration.domain import token_base

CONCRETE_TOKEN_MODULES = {
    "ebl.transliteration.domain.egyptian_metrical_feet_separator_token",
    "ebl.transliteration.domain.enclosure_tokens",
    "ebl.transliteration.domain.greek_tokens",
    "ebl.transliteration.domain.normalized_akkadian",
    "ebl.transliteration.domain.sign_tokens",
    "ebl.transliteration.domain.sign_token_base",
    "ebl.transliteration.domain.named_signs",
    "ebl.transliteration.domain.tokens",
    "ebl.transliteration.domain.unknown_sign_tokens",
    "ebl.transliteration.domain.word_tokens",
}


def _imported_modules() -> Set[str]:
    tree = ast.parse(Path(str(token_base.__file__)).read_text(encoding="utf-8"))
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


def test_token_base_does_not_import_any_concrete_token_module() -> None:
    assert _imported_modules() & CONCRETE_TOKEN_MODULES == set()


def test_token_base_has_no_type_checking_guard() -> None:
    source = Path(str(token_base.__file__)).read_text(encoding="utf-8")

    assert "TYPE_CHECKING" not in source


def test_the_concrete_token_modules_import_token_base_one_way() -> None:
    from ebl.transliteration.domain import enclosure_tokens, word_tokens

    for module in (enclosure_tokens, word_tokens):
        source = Path(str(module.__file__)).read_text(encoding="utf-8")
        imported = {
            node.module
            for node in ast.walk(ast.parse(source))
            if isinstance(node, ast.ImportFrom) and node.module
        }
        assert imported & {
            "ebl.transliteration.domain.token_base",
            "ebl.transliteration.domain.tokens",
        }
