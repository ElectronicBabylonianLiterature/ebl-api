from enum import Enum, unique


@unique
class Genre(Enum):
    LITERATURE = "L"
    DIVINATION = "D"
    LEXICOGRAPHY = "Lex"
    MAGIC = "Mag"
    MEDICINE = "Med"
    SHUILA = "Šui"
