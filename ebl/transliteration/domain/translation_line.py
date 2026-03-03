from typing import Optional, Sequence

import attr
import pydash

from ebl.lemmatization.domain.lemmatization import LemmatizationToken
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.label_validator import validate_labels
from ebl.transliteration.domain.labels import ColumnLabel, Label, SurfaceLabel
from ebl.transliteration.domain.line import Line
from ebl.transliteration.domain.line_number import AbstractLineNumber
from ebl.transliteration.domain.markup import MarkupPart, convert_part_sequence

DEFAULT_LANGUAGE = "en"


@attr.s(frozen=True, auto_attribs=True)
class Extent:
    number: AbstractLineNumber
    labels: Sequence[Label] = attr.ib(default=(), validator=validate_labels)

    @property
    def column(self) -> Optional[ColumnLabel]:
        return pydash.head(
            [label for label in self.labels if isinstance(label, ColumnLabel)]
        )

    @property
    def surface(self) -> Optional[SurfaceLabel]:
        return pydash.head(
            [label for label in self.labels if isinstance(label, SurfaceLabel)]
        )

    def __str__(self) -> str:
        labels = (
            f"{' '.join(label.to_value() for label in self.labels)} "
            if self.labels
            else ""
        )
        return f"{labels}{self.number.label}"


@attr.s(frozen=True, auto_attribs=True)
class TranslationLine(Line):
    parts: Sequence[MarkupPart] = attr.ib(converter=convert_part_sequence)
    language: str = DEFAULT_LANGUAGE
    extent: Optional[Extent] = None

    @property
    def translation(self) -> str:
        return "".join(part.value for part in self.parts)

    @property
    def prefix(self) -> str:
        extent = f".({self.extent})" if self.extent else ""
        return f"#tr.{self.language}{extent}: "

    @property
    def atf(self) -> Atf:
        return Atf(f"{self.prefix}{self.translation}")

    @property
    def lemmatization(self) -> Sequence[LemmatizationToken]:
        return (LemmatizationToken(self.translation),)
