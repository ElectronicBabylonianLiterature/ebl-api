from abc import ABC, abstractmethod
import re
from typing import Iterable, Pattern, Sequence, Tuple, TypeVar

import attr
import pydash

from ebl.bibliography.domain.reference import BibliographyId, Reference, ReferenceType
from ebl.transliteration.domain.atf_visitor import convert_to_atf
from ebl.transliteration.domain.enclosure_visitor import set_enclosure_type
from ebl.transliteration.domain.language import Language
from ebl.transliteration.domain.language_visitor import set_language
from ebl.transliteration.domain.tokens import Token


SPECIAL_CHARACTERS: Pattern[str] = re.compile(r"[@{}\\]")
PUNCTUATION: str = ";,:.-–—"


def escape(unescaped: str) -> str:
    return SPECIAL_CHARACTERS.sub(lambda match: f"\\{match.group(0)}", unescaped)


MARKUP = TypeVar("MARKUP", bound="MarkupPart")
TEXT = TypeVar("TEXT", bound="TextPart")


@attr.s(frozen=True, auto_attribs=True)
class MarkupPart(ABC):
    @property
    @abstractmethod
    def value(self) -> str:
        ...

    @property
    def key(self) -> str:
        return self.value

    def rstrip(self: MARKUP) -> MARKUP:
        return self

    def title_case(self: MARKUP) -> MARKUP:
        return self


@attr.s(frozen=True, auto_attribs=True)
class TextPart(MarkupPart):
    text: str

    def rstrip(self: TEXT) -> TEXT:
        return attr.evolve(self, text=self.text.rstrip(PUNCTUATION))

    def title_case(self: TEXT) -> TEXT:
        return attr.evolve(self, text=pydash.title_case(self.text))


@attr.s(frozen=True, auto_attribs=True)
class StringPart(TextPart):
    @property
    def value(self) -> str:
        return self.text


@attr.s(frozen=True, auto_attribs=True)
class EmphasisPart(TextPart):
    @property
    def value(self) -> str:
        return f"@i{{{self.text}}}"


@attr.s(frozen=True, auto_attribs=True)
class LanguagePart(MarkupPart):
    language: Language = attr.ib()
    tokens: Sequence[Token] = attr.ib(converter=tuple)

    @property
    def code(self) -> str:
        code = {
            Language.AKKADIAN: "akk",
            Language.SUMERIAN: "sux",
            Language.EMESAL: "es",
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
        language: Language, tokens: Sequence[Token]
    ) -> "LanguagePart":
        tokens_with_enclosures = set_enclosure_type(tokens)
        tokens_with_language = set_language(tokens_with_enclosures, language)

        return LanguagePart(language, tokens_with_language)


@attr.s(auto_attribs=True, frozen=True)
class BibliographyPart(MarkupPart):
    reference: Reference = attr.ib()

    @reference.validator
    def validate_reference(self, _attribute, value: Reference) -> None:
        is_type_invalid = value.type != ReferenceType.DISCUSSION
        is_notes_invalid = value.notes != ""
        is_lines_invalid = len(value.lines_cited) != 0

        if is_type_invalid or is_notes_invalid or is_lines_invalid:
            raise ValueError(
                "The reference must be a DISCUSSION without notes or lines cited."
            )

    @property
    def value(self) -> str:
        id = escape(self.reference.id)
        pages = escape(self.reference.pages)
        return f"@bib{{{id}@{pages}}}"

    @staticmethod
    def of(id: BibliographyId, pages: str) -> "BibliographyPart":
        return BibliographyPart(Reference(id, ReferenceType.DISCUSSION, pages))


def convert_part_sequence(parts: Iterable[MarkupPart]) -> Tuple[MarkupPart, ...]:
    return tuple(parts)
