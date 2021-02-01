import pytest  # pyre-ignore[21]

from ebl.transliteration.domain.parallel_line import ParallelFragment
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.lemmatization import LemmatizationToken
from ebl.fragmentarium.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.atf import Surface


@pytest.mark.parametrize(  # pyre-ignore[56]
    "cf,duplicates,surface,display_value",
    [(True, True, Surface.OBVERSE, "cf. K.1 &d o 1"), (False, False, None, "K.1 1")],
)
def test_parallel_fragment(cf, duplicates, surface, display_value) -> None:
    museum_number = MuseumNumber.of("K.1")
    line_number = LineNumber(1)
    line = ParallelFragment(cf, museum_number, duplicates, surface, line_number)

    assert line.has_cf is cf
    assert line.museum_number == museum_number
    assert line.has_duplicates is duplicates
    assert line.surface == surface
    assert line.line_number == line_number

    assert line.display_value == display_value
    assert line.atf == Atf(f"// {display_value}")
    assert line.lemmatization == (LemmatizationToken(display_value),)
