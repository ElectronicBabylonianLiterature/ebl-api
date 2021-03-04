from typing import Iterable

import pytest

from ebl.corpus.domain.manuscript import Period, Provenance, ManuscriptType, Siglum
from ebl.corpus.domain.chapter_transformer import ChapterTransformer
from ebl.transliteration.domain.atf import Surface
from ebl.transliteration.domain.lark_parser import CHAPTER_PARSER
from ebl.transliteration.domain.labels import Label, ColumnLabel, SurfaceLabel


def parse_siglum(siglum):
    tree = CHAPTER_PARSER.parse(siglum, start="siglum")
    return ChapterTransformer().transform(tree)


@pytest.mark.parametrize("period", [Period.NEO_ASSYRIAN])
@pytest.mark.parametrize("provenance", [Provenance.DILBAT, Provenance.PERIPHERY])
#  pyre-ignore[56]
@pytest.mark.parametrize("type_", [ManuscriptType.SCHOOL, ManuscriptType.LIBRARY])
@pytest.mark.parametrize("disambiquator", ["", "a"])
def test_parse_siglum(
    period: Period, provenance: Provenance, type_: ManuscriptType, disambiquator
) -> None:
    assert parse_siglum(
        f"{provenance.abbreviation}{period.abbreviation}{type_.abbreviation}{disambiquator}"
    ) == Siglum(provenance, period, type_, disambiquator)


def parse_label(labels):
    tree = CHAPTER_PARSER.parse(labels, start="labels")
    return ChapterTransformer().transform(tree)


@pytest.mark.parametrize(  # pyre-ignore[56]
    "labels",
    [
        (ColumnLabel.from_int(3),),
        (SurfaceLabel.from_label(Surface.OBVERSE),),
        (SurfaceLabel.from_label(Surface.OBVERSE), ColumnLabel.from_int(3)),
    ],
)
def test_parse_label(labels: Iterable[Label]) -> None:
    assert parse_label(" ".join(label.to_value() for label in labels)) == labels
