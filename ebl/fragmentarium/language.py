from enum import Enum, auto


class Language(Enum):
    UNKNOWN = 0
    AKKADIAN = auto()
    SUMERIAN = auto()
    EMESAL = auto()

    @property
    def lemmatizable(self) -> bool:
        return self.name in ['UNKNOWN', 'AKKADIAN']

    @classmethod
    def of_atf(cls, code: str) -> 'Language':
        codes = {
            r'%sux': cls.SUMERIAN,
            r'%es': cls.EMESAL,
            r'%sb': cls.AKKADIAN
        }
        return codes.get(code, cls.UNKNOWN)
