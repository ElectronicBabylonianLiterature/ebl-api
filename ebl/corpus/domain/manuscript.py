from typing import Optional, Sequence

import attr

from ebl.bibliography.domain.reference import Reference
from ebl.common.domain.period import Period, PeriodModifier
from ebl.common.domain.manuscript_type import ManuscriptType
from ebl.common.domain.provenance import Provenance
from ebl.fragmentarium.domain.joins import Joins
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine


@attr.s(auto_attribs=True, frozen=True)
class Siglum:
    provenance: Provenance
    period: Period
    type: ManuscriptType
    disambiquator: str

    def __str__(self) -> str:
        return "".join(
            [
                self.provenance.abbreviation,
                self.period.abbreviation,
                self.type.abbreviation,
                self.disambiquator,
            ]
        )


@attr.s(auto_attribs=True, frozen=True)
class OldSiglum:
    siglum: str
    reference: Reference


def is_invalid_standard_text(provenance, period, type_) -> bool:
    return provenance is Provenance.STANDARD_TEXT and (
        period is not Period.NONE or type_ is not ManuscriptType.NONE
    )


def is_invalid_non_standard_text(provenance, period, type_) -> bool:
    return provenance is not Provenance.STANDARD_TEXT and (
        period is Period.NONE or type_ is ManuscriptType.NONE
    )


@attr.s(auto_attribs=True, frozen=True)
class Manuscript:
    id: int
    siglum_disambiguator: str = ""
    old_sigla: Sequence[OldSiglum] = tuple()
    museum_number: Optional[MuseumNumber] = None
    accession: str = attr.ib(default="")
    period_modifier: PeriodModifier = PeriodModifier.NONE
    period: Period = Period.NEO_ASSYRIAN
    provenance: Provenance = attr.ib(default=Provenance.NINEVEH)
    type: ManuscriptType = ManuscriptType.LIBRARY
    notes: str = ""
    colophon: Text = Text()
    unplaced_lines: Text = Text()
    references: Sequence[Reference] = tuple()
    joins: Joins = Joins()
    is_in_fragmentarium: bool = False

    @accession.validator
    def validate_accession(self, _, value) -> None:
        if self.museum_number and value:
            raise ValueError("Accession given when museum number present.")

    @provenance.validator
    def validate_provenance(self, _, value) -> None:
        if is_invalid_standard_text(value, self.period, self.type):
            raise ValueError(
                "Manuscript must not have period and type when provenance is Standard Text."
            )
        elif is_invalid_non_standard_text(value, self.period, self.type):
            raise ValueError(
                "Manuscript must have period and type unless provenance is Standard Text."
            )

    @property
    def text_lines(self) -> Sequence[TextLine]:
        return [*self.colophon.text_lines, *self.unplaced_lines.text_lines]

    @property
    def siglum(self) -> Siglum:
        return Siglum(
            self.provenance, self.period, self.type, self.siglum_disambiguator
        )
