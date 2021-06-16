import pytest
from ebl.corpus.domain.manuscript import Manuscript, ManuscriptType, Period, Provenance
from ebl.fragmentarium.domain.museum_number import MuseumNumber


@pytest.mark.parametrize(  # pyre-ignore[56]
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
    with pytest.raises(ValueError):
        Manuscript(1, provenance=provenance, period=period, type=type_)


def test_giving_museum_number_and_accession_is_invalid():
    with pytest.raises(ValueError):
        Manuscript(
            1, museum_number=MuseumNumber("BM", "x"), accession="accession not allowed"
        )
