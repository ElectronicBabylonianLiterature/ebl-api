from typing import Sequence

import attr

from ebl.lemmatization.domain.lemmatization import LemmatizationToken


@attr.s(auto_attribs=True, frozen=True)
class LineVariantLemmatization:
    reconstruction: Sequence[LemmatizationToken]
    manuscripts: Sequence[Sequence[LemmatizationToken]]


ChapterLemmatization = Sequence[Sequence[LineVariantLemmatization]]
