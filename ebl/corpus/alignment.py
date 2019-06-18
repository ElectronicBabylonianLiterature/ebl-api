from typing import Optional, Tuple

import attr


@attr.s(auto_attribs=True, frozen=True)
class AlignmentToken:
    value: str
    alignment: Optional[int]
    has_apparatus_entry: Optional[bool]


@attr.s(auto_attribs=True, frozen=True)
class Alignment:
    lines: Tuple[Tuple[AlignmentToken, ...], ...]

    @staticmethod
    def of(data):
        return Alignment(tuple(
            tuple(
                AlignmentToken(
                    token['value'],
                    token.get('alignment'),
                    token.get('hasApparatusEntry')
                )
                for token in line
            )
            for line in data
        ))
