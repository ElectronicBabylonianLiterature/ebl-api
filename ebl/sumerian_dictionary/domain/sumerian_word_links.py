from typing import Sequence

import attr


@attr.s(frozen=True, auto_attribs=True)
class WordLink:
    id: str
    citation_form: str
    homonym: str = ""
    guide_word: str = ""


@attr.s(frozen=True, auto_attribs=True)
class CrossReference:
    relation: str
    target: str
    method: str
    targets: Sequence[WordLink] = ()
    name_targets: Sequence[WordLink] = ()
    ambiguous: bool = False


@attr.s(frozen=True, auto_attribs=True)
class Alias:
    form: str
    relation: str
    entry_id: str
    method: str
    source: str
    meanings: Sequence[str] = ()
    uncertain: bool = False
