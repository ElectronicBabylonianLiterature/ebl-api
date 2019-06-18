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

    @staticmethod
    def from_dict(data):
        return AlignmentToken(
            data['value'],
            data.get('alignment'),
            data.get('hasApparatusEntry')
        )


@attr.s(auto_attribs=True, frozen=True)
class Alignment:
    _lines: Tuple[Tuple[Tuple[AlignmentToken, ...], ...], ...]

    def get_manuscript_line(self, line_index: int, manuscript_index: int):
        return self._lines[line_index][manuscript_index]

    @staticmethod
    def from_dict(data):
        return Alignment(tuple(
            tuple(
                tuple(
                    AlignmentToken.from_dict(token)
                    for token in manuscript
                )
                for manuscript in line
            )
            for line in data
        ))
