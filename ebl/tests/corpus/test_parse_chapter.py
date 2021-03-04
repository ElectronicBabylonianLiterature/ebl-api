import pytest

from ebl.corpus.domain.manuscript import Period, Provenance, ManuscriptType, Siglum
from ebl.corpus.domain.chapter_transformer import ChapterTransformer
from ebl.transliteration.domain.lark_parser import CHAPTER_PARSER


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
