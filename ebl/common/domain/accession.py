from ebl.transliteration.domain.museum_number import MuseumNumber
import functools
import attr
import re


@functools.total_ordering
@attr.s(auto_attribs=True, frozen=True, order=False)
class Accession(MuseumNumber):
    @staticmethod
    def of(source: str) -> "Accession":
        if match := re.compile(r"(.+?)\.([^.]+)(?:\.([^.]+))?").fullmatch(source):
            return Accession(match[1], match[2], match[3] or "")
        else:
            raise ValueError(f"'{source}' is not a valid accession number.")
