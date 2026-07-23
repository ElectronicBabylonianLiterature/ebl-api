from typing import Any, Dict, Iterable, Optional, Sequence, Tuple

import attr
from marshmallow import ValidationError

from ebl.common.domain.period import Period, PeriodModifier
from ebl.fragmentarium.domain.named_entity import NamedEntity, RealiaEntity
from ebl.fragmentarium.domain.genres import genres
from ebl.transliteration.domain.atf_parsers.lark_parser import (
    PARSE_ERRORS,
    parse_markup_paragraphs,
)
from ebl.transliteration.domain.markup import MarkupPart


def parse_markup_with_paragraphs(text: str) -> Sequence[MarkupPart]:
    try:
        return parse_markup_paragraphs(text) if text else ()
    except PARSE_ERRORS as error:
        raise ValidationError(f"Invalid markup: {text}. {error}") from error


class NotLowestJoinError(ValueError):
    pass


@attr.s(auto_attribs=True, frozen=True)
class UncuratedReference:
    document: str
    pages: Sequence[int] = ()
    search_term: Optional[str] = None


@attr.s(auto_attribs=True, frozen=True)
class Measure:
    value: Optional[float] = None
    note: Optional[str] = None


@attr.s(auto_attribs=True, frozen=True)
class Acquisition:
    description: str = ""
    supplier: str = ""
    date: int = 0

    @staticmethod
    def of(source: Dict[str, Any]) -> "Acquisition":
        return Acquisition(
            description=source.get("description", ""),
            supplier=source.get("supplier", ""),
            date=source.get("date", 0),
        )


def _validate_genre_category(_instance, _attribute, category: Sequence[str]) -> None:
    categories = tuple(category)
    if categories not in genres:
        raise ValueError(f"'{categories}' is not a valid genre")


@attr.s(auto_attribs=True, frozen=True)
class Genre:
    category: Sequence[str] = attr.ib(validator=_validate_genre_category)
    uncertain: bool = False


@attr.s(auto_attribs=True, frozen=True)
class MarkupText:
    text: str = ""
    parts: Sequence[MarkupPart] = ()


@attr.s(auto_attribs=True, frozen=True)
class Introduction(MarkupText):
    pass


@attr.s(auto_attribs=True, frozen=True)
class Notes(MarkupText):
    pass


@attr.s(auto_attribs=True, frozen=True)
class Script:
    period: Period = attr.ib(default=Period.NONE)
    period_modifier: PeriodModifier = attr.ib(default=PeriodModifier.NONE)
    uncertain: bool = False

    def __str__(self) -> str:
        return self.abbreviation

    @property
    def abbreviation(self) -> str:
        return self.period.value[1]


@attr.s(auto_attribs=True, frozen=True)
class DossierReference:
    dossierId: str
    isUncertain: bool = False


def to_named_entity_tuple(
    value: Iterable[NamedEntity],
) -> Tuple[NamedEntity, ...]:
    return tuple(value)


def to_realia_tuple(value: Iterable[RealiaEntity]) -> Tuple[RealiaEntity, ...]:
    return tuple(value)
