from typing import Union

import pytest
from ebl.common.domain.period import Period

from ebl.corpus.domain.manuscript import Manuscript
from ebl.corpus.domain.manuscript_type import ManuscriptType
from ebl.common.domain.provenance import Provenance
from ebl.tests.factories.corpus import ManuscriptLineFactory
from ebl.transliteration.domain.line import EmptyLine
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.text_line import TextLine


@pytest.mark.parametrize(
    "line,expected",
    [(EmptyLine(), True), (TextLine(LineNumber(1)), False)],
)
def test_is_empty(line: Union[TextLine, EmptyLine], expected: bool) -> None:
    assert ManuscriptLineFactory.build(line=line).is_empty is expected


@pytest.mark.parametrize(
    "provenance,period,type_",
    [
        (Provenance.STANDARD_TEXT, Period.OLD_ASSYRIAN, ManuscriptType.NONE),
        (Provenance.STANDARD_TEXT, Period.NONE, ManuscriptType.LIBRARY),
        (Provenance.STANDARD_TEXT, Period.OLD_ASSYRIAN, ManuscriptType.SCHOOL),
        (Provenance.ASSYRIA, Period.OLD_ASSYRIAN, ManuscriptType.NONE),
        (Provenance.MEGIDDO, Period.NONE, ManuscriptType.LIBRARY),
        (Provenance.UNCERTAIN, Period.NONE, ManuscriptType.NONE),
    ],
)
def test_invalid_siglum(provenance, period, type_) -> None:
    with pytest.raises(ValueError):  # pyre-ignore[16]
        Manuscript(1, provenance=provenance, period=period, type=type_)


def test_giving_museum_number_and_accession_is_invalid():
    with pytest.raises(ValueError):
        Manuscript(
            1, museum_number=MuseumNumber("BM", "x"), accession="accession not allowed"
        )
