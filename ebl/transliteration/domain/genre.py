from enum import Enum, unique


@unique
class Genre(Enum):
    LITERATURE = "L"
    DIVINATION = "D"
    LEXICOGRAPHY = "Lex"
    MEDICINE = "Med"
