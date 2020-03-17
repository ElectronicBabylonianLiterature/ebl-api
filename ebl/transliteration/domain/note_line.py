from abc import ABC, abstractmethod
from typing import Sequence

import attr

from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.tokens import ValueToken


@attr.s(frozen=True, auto_attribs=True)
class NotePart(ABC):
    text: str

    @property
    @abstractmethod
    def value(self) -> str:
        ...


class StringPart(NotePart):
    @property
    def value(self) -> str:
        return self.text


@attr.s(frozen=True)
class EmphasisPart(NotePart):
    @property
    def value(self) -> str:
        return f"@i{{{self.text}}}"


@attr.s(frozen=True, auto_attribs=True)
class LanguagePart(NotePart):
    language: Language = attr.ib()

    @language.validator
    def _check_language(self, attribute, value):
        if value not in [Language.AKKADIAN, Language.SUMERIAN]:
            raise ValueError("language must be AKKADIAN or SUMERIAN")

    @property
    def value(self) -> str:
        code = {Language.AKKADIAN: "akk", Language.SUMERIAN: "sux"}[self.language]
        return f"@{code}{{{self.text}}}"


@attr.s(frozen=True, auto_attribs=True)
class NoteLine(Line):
    parts: Sequence[NotePart]

    @property
    def prefix(self) -> str:
        return "#note: "

    @property
    def content(self) -> Sequence[ValueToken]:
        return [ValueToken.of(part.value) for part in self.parts]

    @property
    def atf(self) -> Atf:
        note = "".join(part.value for part in self.parts)
        return Atf(f"{self.prefix}{note}")
