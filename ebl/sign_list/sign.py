from typing import Optional, Tuple

import attr


@attr.s(frozen=True, auto_attribs=True)
class SignListRecord:
    name: str
    number: str


@attr.s(frozen=True, auto_attribs=True)
class Value:
    value: str
    sub_index: Optional[int] = None


@attr.s(frozen=True, auto_attribs=True)
class Sign:
    name: str
    lists: Tuple[SignListRecord, ...]
    values: Tuple[Value, ...]
