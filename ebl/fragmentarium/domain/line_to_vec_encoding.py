from enum import Enum
from typing import Sequence, Tuple


class LineToVecEncoding(Enum):
    START = 0
    TEXT_LINE = 1
    SINGLE_RULING = 2
    DOUBLE_RULING = 3
    TRIPLE_RULING = 4
    END = 5

    @staticmethod
    def from_list(sequence: Sequence[int]) -> Tuple["LineToVecEncoding", ...]:
        return tuple(map(LineToVecEncoding, sequence))


LineToVecEncodings = Tuple[LineToVecEncoding, ...]
