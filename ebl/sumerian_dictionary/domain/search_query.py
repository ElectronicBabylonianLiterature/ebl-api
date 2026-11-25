from enum import Enum
from typing import FrozenSet

import attr

DEFAULT_LIMIT = 25
MAXIMUM_LIMIT = 100

PROPER_NOUN_TAGS: FrozenSet[str] = frozenset(
    {
        "DN",
        "PN",
        "TN",
        "SN",
        "RN",
        "GN",
        "WN",
        "MN",
        "ON",
        "CN",
        "EN",
        "FN",
        "QN",
        "LN",
    }
)


class Kind(Enum):
    ALL = "all"
    WORDS = "words"
    NAMES = "names"


class SourceFilter(Enum):
    ANY = "any"
    ATTINGER = "attinger"
    EPSD2 = "epsd2"


@attr.s(frozen=True, auto_attribs=True)
class SumerianWordQuery:
    query: str
    kind: Kind = Kind.ALL
    source: SourceFilter = SourceFilter.ANY
    limit: int = DEFAULT_LIMIT
    offset: int = 0
