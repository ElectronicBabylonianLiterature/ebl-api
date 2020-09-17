from typing import Optional, Sequence

import attr


class AlignmentError(Exception):
    def __init__(self):
        super().__init__("Invalid alignment")


@attr.s(auto_attribs=True, frozen=True)
class AlignmentToken:
    value: str
    alignment: Optional[int]

    @staticmethod
    def from_dict(data):
        return AlignmentToken(data["value"], data.get("alignment"))


@attr.s(auto_attribs=True, frozen=True)
class Alignment:
    _lines: Sequence[Sequence[Sequence[AlignmentToken]]]

    def get_line(self, line_index: int) -> Sequence[Sequence[AlignmentToken]]:
        return self._lines[line_index]

    def get_manuscript_line(
        self, line_index: int, manuscript_index: int
    ) -> Sequence[AlignmentToken]:
        return self.get_line(line_index)[manuscript_index]

    def get_number_of_lines(self) -> int:
        return len(self._lines)

    def get_number_of_manuscripts(self, line_index: int) -> int:
        return len(self.get_line(line_index))

    @staticmethod
    def from_dict(data):
        return Alignment(
            tuple(
                tuple(
                    tuple(AlignmentToken.from_dict(token) for token in manuscript)
                    for manuscript in line
                )
                for line in data
            )
        )
