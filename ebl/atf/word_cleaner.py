import re

from ebl.atf.atf import ATF_EXTENSIONS, FLAGS, LACUNA

IGNORE = [
        LACUNA['begin'],
        r'\(',
        r'\)',
        LACUNA['end'],
        FLAGS['uncertainty'],
        FLAGS['collation'],
        FLAGS['damage'],
        FLAGS['correction'],
        ATF_EXTENSIONS['erasure_illegible'],
        ATF_EXTENSIONS['erasure_boundary']
    ]
IGNORE_REGEX = f'({"|".join(IGNORE)})*'


def clean_word(word: str) -> str:
    return re.sub(IGNORE_REGEX, '', word)
