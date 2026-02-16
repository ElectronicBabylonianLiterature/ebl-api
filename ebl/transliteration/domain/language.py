from enum import Enum, auto


class Language(Enum):
    UNKNOWN = 0
    AKKADIAN = auto()
    HITTITE = auto()
    SUMERIAN = auto()
    EMESAL = auto()
    GREEK = auto()

    @property
    def lemmatizable(self) -> bool:
        return self.name in ["UNKNOWN", "AKKADIAN"]

    @classmethod
    def of_atf(cls, code: str) -> "Language":
        codes = {
            "%ma": Language.AKKADIAN,
            "%mb": Language.AKKADIAN,
            "%na": Language.AKKADIAN,
            "%nb": Language.AKKADIAN,
            "%lb": Language.AKKADIAN,
            "%sb": Language.AKKADIAN,
            "%a": Language.AKKADIAN,
            "%akk": Language.AKKADIAN,
            "%eakk": Language.AKKADIAN,
            "%oakk": Language.AKKADIAN,
            "%ur3akk": Language.AKKADIAN,
            "%oa": Language.AKKADIAN,
            "%ob": Language.AKKADIAN,
            "%sux": Language.SUMERIAN,
            "%es": Language.EMESAL,
            "%e": Language.EMESAL,
            "%n": Language.AKKADIAN,
            "%akkgrc": Language.AKKADIAN,
            "%suxgrc": Language.SUMERIAN,
            "%grc": Language.GREEK,
            "%hit": Language.HITTITE,
        }
        return codes.get(code, cls.UNKNOWN)


DEFAULT_LANGUAGE: Language = Language.AKKADIAN
