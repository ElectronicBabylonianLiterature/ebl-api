from typing import List, Tuple

from ebl.transliteration.domain.language import DEFAULT_LANGUAGE, Language

LANGUAGE_SHIFT_CASES: List[Tuple[str, Language]] = [
    ("%ma", Language.AKKADIAN),
    ("%mb", Language.AKKADIAN),
    ("%na", Language.AKKADIAN),
    ("%nb", Language.AKKADIAN),
    ("%lb", Language.AKKADIAN),
    ("%sb", Language.AKKADIAN),
    ("%a", Language.AKKADIAN),
    ("%akk", Language.AKKADIAN),
    ("%eakk", Language.AKKADIAN),
    ("%oakk", Language.AKKADIAN),
    ("%ur3akk", Language.AKKADIAN),
    ("%oa", Language.AKKADIAN),
    ("%ob", Language.AKKADIAN),
    ("%sux", Language.SUMERIAN),
    ("%es", Language.EMESAL),
    ("%hit", Language.HITTITE),
    ("%foo", DEFAULT_LANGUAGE),
]
