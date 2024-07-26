from abc import ABC, abstractmethod
import re
from typing import Iterable, Pattern, Sequence, Tuple, TypeVar

import attr

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


def titlecase(text: str) -> str:
    return re.sub(
        r"\w+([\[\]'’]\w+)?",
        lambda word: word.group(0).capitalize(),
        text,
    )


MP = TypeVar("MP", bound="MarkupPart")
TP = TypeVar("TP", bound="TextPart")


@attr.s(frozen=True, auto_attribs=True)
class MarkupPart(ABC):
    @property
    @abstractmethod
    def value(self) -> str: ...

    @property
    def key(self) -> str:
        return self.value

    def rstrip(self: MP) -> MP:
        return self

    def title_case(self: MP) -> MP:
        return self


@attr.s(frozen=True, auto_attribs=True)
class TextPart(MarkupPart):
    text: str

    def rstrip(self: TP) -> TP:
        return attr.evolve(self, text=self.text.rstrip(PUNCTUATION))

    def title_case(self: TP) -> TP:
        return attr.evolve(self, text=titlecase(self.text))


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
        pages = f"@{escape(self.reference.pages)}"
        return f"@bib{{{id}{'' if pages == '@' else pages}}}"

    @staticmethod
    def of(id: BibliographyId, pages: str) -> "BibliographyPart":
        return BibliographyPart(Reference(id, ReferenceType.DISCUSSION, pages))


@attr.s(frozen=True, auto_attribs=True)
class ParagraphPart(MarkupPart):
    @property
    def value(self) -> str:
        return "\n\n"


@attr.s(frozen=True, auto_attribs=True)
class UrlPart(TextPart):
    url: str

    @property
    def value(self) -> str:
        return "".join((f"@url{{{self.url}}}", f"{{{self.text}}}" if self.text else ""))


def convert_part_sequence(parts: Iterable[MarkupPart]) -> Tuple[MarkupPart, ...]:
    return tuple(parts)


def rstrip(parts: Sequence[MarkupPart]) -> Sequence[MarkupPart]:
    if parts:
        *head, last = parts
        return (*head, last.rstrip())
    return []


def title_case(parts: Sequence[MarkupPart]) -> Sequence[MarkupPart]:
    return tuple(part.title_case() for part in parts)


def to_title(parts: Sequence[MarkupPart]) -> Sequence[MarkupPart]:
    return title_case(rstrip(parts))
