from typing import Optional, Tuple

import attr


class AlignmentError(Exception):
    def __init__(self):
        super().__init__('Invalid alignment')


@attr.s(auto_attribs=True, frozen=True)
class AlignmentToken:
    value: str
    alignment: Optional[int]
    has_apparatus_entry: Optional[bool] = attr.ib()

    @has_apparatus_entry.validator
    def _check_has_apparatus_entry(self, attribute, value):
        if value is None and self.alignment is not None:
            raise ValueError(
                'has_apparatus_entry cannot be None if alignment is not None.'
            )
        elif value is not None and self.alignment is None:
            raise ValueError(
                'has_apparatus_entry must be None if alignment is None.'
            )

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

    def get_line(self,
                 line_index: int) -> Tuple[Tuple[AlignmentToken, ...], ...]:
        return self._lines[line_index]

    def get_manuscript_line(
            self, line_index: int, manuscript_index: int
    ) -> Tuple[AlignmentToken, ...]:
        return self.get_line(line_index)[manuscript_index]

    def get_number_of_lines(self) -> int:
        return len(self._lines)

    def get_number_of_manuscripts(self, line_index: int) -> int:
        return len(self.get_line(line_index))

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
