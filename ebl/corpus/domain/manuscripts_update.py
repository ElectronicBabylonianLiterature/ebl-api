from typing import Sequence

import attr

from ebl.corpus.domain.manuscript import Manuscript
from ebl.transliteration.domain.museum_number import MuseumNumber


@attr.s(auto_attribs=True, frozen=True)
class ManuscriptsUpdate:
    manuscripts: Sequence[Manuscript]
    uncertain_fragments: Sequence[MuseumNumber]
