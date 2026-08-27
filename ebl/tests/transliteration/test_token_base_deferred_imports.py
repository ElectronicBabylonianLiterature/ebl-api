import typing
from pathlib import Path
from typing import Any, Dict

import pytest

from ebl.transliteration.domain import token_base
from ebl.transliteration.domain.egyptian_metrical_feet_separator_token import (
    EgyptianMetricalFeetSeparator,
)
from ebl.transliteration.domain.enclosure_tokens import (
    AccidentalOmission,
    BrokenAway,
    DocumentOrientedGloss,
    Emendation,
    Erasure,
    Gloss,
    IntentionalOmission,
    PerhapsBrokenAway,
    Removal,
)
from ebl.transliteration.domain.greek_tokens import GreekWord
from ebl.transliteration.domain.normalized_akkadian import (
    AkkadianWord,
    Caesura,
    MetricalFootSeparator,
)
from ebl.transliteration.domain.sign_tokens import (
    CompoundGrapheme,
    Divider,
    Grapheme,
    NamedSign,
    Number,
)
from ebl.transliteration.domain.tokens import (
    CommentaryProtocol,
    LanguageShift,
    LineBreak,
    Variant,
)
from ebl.transliteration.domain.unknown_sign_tokens import UnknownSign
from ebl.transliteration.domain.word_tokens import Word

DEFERRED_TOKEN_TYPES = {
    "AccidentalOmission": AccidentalOmission,
    "AkkadianWord": AkkadianWord,
    "BrokenAway": BrokenAway,
    "Caesura": Caesura,
    "CommentaryProtocol": CommentaryProtocol,
    "CompoundGrapheme": CompoundGrapheme,
    "Divider": Divider,
    "DocumentOrientedGloss": DocumentOrientedGloss,
    "EgyptianMetricalFeetSeparator": EgyptianMetricalFeetSeparator,
    "Emendation": Emendation,
    "Erasure": Erasure,
    "Gloss": Gloss,
    "Grapheme": Grapheme,
    "GreekWord": GreekWord,
    "IntentionalOmission": IntentionalOmission,
    "LanguageShift": LanguageShift,
    "LineBreak": LineBreak,
    "MetricalFootSeparator": MetricalFootSeparator,
    "NamedSign": NamedSign,
    "Number": Number,
    "PerhapsBrokenAway": PerhapsBrokenAway,
    "Removal": Removal,
    "UnknownSign": UnknownSign,
    "Variant": Variant,
    "Word": Word,
}


def _execute_token_base_as_a_type_checker_sees_it(
    monkeypatch: pytest.MonkeyPatch,
) -> Dict[str, Any]:
    monkeypatch.setattr(typing, "TYPE_CHECKING", True)
    path = Path(token_base.__file__)
    namespace: Dict[str, Any] = {
        "__name__": "token_base_deferred_import_probe",
        "__file__": str(path),
    }
    exec(compile(path.read_text(encoding="utf-8"), str(path), "exec"), namespace)
    return namespace


def test_every_deferred_import_resolves_to_the_annotated_class(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    namespace = _execute_token_base_as_a_type_checker_sees_it(monkeypatch)

    resolved = {name: namespace.get(name) for name in DEFERRED_TOKEN_TYPES}

    assert resolved == DEFERRED_TOKEN_TYPES


def test_the_deferred_imports_do_not_run_when_type_checking_is_off() -> None:
    assert typing.TYPE_CHECKING is False
    assert not hasattr(token_base, "Word")
