from typing import Optional, Tuple

import attr


class AlignmentError(Exception):
    def __init__(self):
        super().__init__('Invalid alignment')


@attr.s(auto_attribs=True, frozen=True)
class AlignmentToken:
    value: str
    alignment: Optional[int]
    has_apparatus_entry: Optional[bool]


@attr.s(auto_attribs=True, frozen=True)
class Alignment:
    lines: Tuple[Tuple[Tuple[AlignmentToken, ...], ...], ...]

    @staticmethod
    def of(data):
        return Alignment(tuple(
            tuple(
                tuple(
                    AlignmentToken(
                        token['value'],
                        token.get('alignment'),
                        token.get('hasApparatusEntry')
                    )
                    for token in manuscript
                )
                for manuscript in line
            )
            for line in data
        ))
