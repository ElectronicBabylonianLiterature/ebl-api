from typing import Tuple

import attr

from ebl.fragmentarium.domain.line_to_vec_encoding import LineToVecEncodings
from ebl.fragmentarium.domain.museum_number import MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class LineToVecEntry:
    museum_number: MuseumNumber
    script: str
    line_to_vec: Tuple[LineToVecEncodings, ...]


@attr.s(auto_attribs=True, frozen=True)
class LineToVecScore:
    museum_number: MuseumNumber
    script: str
    score: int
