import attr
from typing import Sequence


@attr.s(frozen=True, auto_attribs=True)
class RealiaInfo:
    realia_id: str
    lemma: str
    type: Sequence[str] = ()
