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
    lists: Tuple[SignListRecord, ...] = tuple()
    values: Tuple[Value, ...] = tuple()

    @property
    def standardization(self):
        standardization_list = 'ABZ'
        try:
            return [f'{record.name}{record.number}'
                    for record
                    in self.lists
                    if record.name == standardization_list][0]
        except IndexError:
            return self.name
