import re

from ebl.transliteration.domain.atf import (
    ATF_EXTENSIONS,
    FLAGS,
    PERHAPS_BROKEN_AWAY,
    BROKEN_AWAY,
)
from ebl.transliteration.domain.side import Side

IGNORE = [
    re.escape(PERHAPS_BROKEN_AWAY[Side.LEFT]),
    re.escape(PERHAPS_BROKEN_AWAY[Side.RIGHT]),
    re.escape(BROKEN_AWAY[Side.LEFT]),
    re.escape(BROKEN_AWAY[Side.RIGHT]),
    FLAGS["uncertainty"],
    FLAGS["collation"],
    FLAGS["damage"],
    FLAGS["correction"],
    ATF_EXTENSIONS["erasure_illegible"],
    ATF_EXTENSIONS["erasure_boundary"],
]
IGNORE_REGEX = f'({"|".join(IGNORE)})*'


def clean_word(word: str) -> str:
    return re.sub(IGNORE_REGEX, "", word)
