from abc import ABC, abstractmethod
import re
from typing import Iterable, Sequence, Tuple

import attr

from ebl.bibliography.domain.reference import BibliographyId, Reference, ReferenceType
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.atf_visitor import convert_to_atf
from ebl.transliteration.domain.enclosure_visitor import set_enclosure_type
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.language_visitor import set_language
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.tokens import Token, ValueToken


SPECIAL_CHARACTERS = re.compile(r"[@{}\\]")


def escape(unescaped: str) -> str:
    return SPECIAL_CHARACTERS.sub(lambda match: f"\\{match.group(0)}", unescaped)


@attr.s(frozen=True, auto_attribs=True)
class NotePart(ABC):
    @property
    @abstractmethod
    def value(self) -> str:
        ...

    @property
    def key(self) -> str:
        return self.value


@attr.s(frozen=True, auto_attribs=True)
class StringPart(NotePart):
    text: str

    @property
    def value(self) -> str:
        return self.text


@attr.s(frozen=True, auto_attribs=True)
class EmphasisPart(NotePart):
    text: str

    @property
    def value(self) -> str:
        return f"@i{{{self.text}}}"


@attr.s(frozen=True, auto_attribs=True)
class LanguagePart(NotePart):
    language: Language = attr.ib()
    tokens: Sequence[Token] = attr.ib(converter=tuple)

    @property
    def code(self) -> str:
        code = {
            Language.AKKADIAN: "akk",
            Language.SUMERIAN: "sux",
            Language.EMESAL: "es"
        }[self.language]

        return f"@{code}"

    @property
    def value(self) -> str:
        transliteration = convert_to_atf(None, self.tokens)
        return f"{self.code}{{{transliteration}}}"

    @property
    def key(self) -> str:
        tokens = "⁚".join(token.get_key() for token in self.tokens)
        return f"{self.code}⟨{tokens}⟩"

    @staticmethod
    def of_transliteration(
        language: Language,
        tokens: Sequence[Token]
    ) -> "LanguagePart":
        tokens_with_enclosures = set_enclosure_type(tokens)
        tokens_with_language = set_language(
            tokens_with_enclosures,
            language
        )

        return LanguagePart(language, tokens_with_language)


@attr.s(auto_attribs=True, frozen=True)
class BibliographyPart(NotePart):
    reference: Reference = attr.ib()

    @reference.validator
    def validate_reference(self, _attribute, value: Reference) -> None:
        is_type_invalid = value.type != ReferenceType.DISCUSSION
        is_notes_invalid = value.notes != ""
        is_lines_invalid = len(value.lines_cited) != 0

        if is_type_invalid or is_notes_invalid or is_lines_invalid:
            raise ValueError("The reference must be a DISCUSSION without notes or lines cited.")

    @property
    def value(self) -> str:
        id = escape(self.reference.id)
        pages = escape(self.reference.pages)
        return f"@bib{{{id}@{pages}}}"

    @staticmethod
    def of(id: BibliographyId, pages: str) -> "BibliographyPart":
        return BibliographyPart(
            Reference(id, ReferenceType.DISCUSSION, pages)
        )


def convert_part_sequence(flags: Iterable[NotePart]) -> Tuple[NotePart, ...]:
    return tuple(flags)


@attr.s(frozen=True, auto_attribs=True)
class NoteLine(Line):
    parts: Sequence[NotePart] = attr.ib(converter=convert_part_sequence)

    @property
    def content(self) -> Sequence[ValueToken]:
        return [ValueToken.of(part.value) for part in self.parts]

    @property
    def key(self) -> str:
        parts = "⁚".join(part.key for part in self.parts)
        return f"NoteLine⁞{self.atf}⟨{parts}⟩"

    @property
    def atf(self) -> Atf:
        note = "".join(part.value for part in self.parts)
        return Atf(f"#note: {note}")
