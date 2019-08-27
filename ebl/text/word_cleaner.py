import re

from ebl.text.atf import ATF_EXTENSIONS, ATF_SPEC

IGNORE = [
        ATF_SPEC['lacuna']['begin'],
        r'\(',
        r'\)',
        ATF_SPEC['lacuna']['end'],
        ATF_SPEC['flags']['uncertainty'],
        ATF_SPEC['flags']['collation'],
        ATF_SPEC['flags']['damage'],
        ATF_SPEC['flags']['correction'],
        ATF_EXTENSIONS['erasure_illegible'],
        ATF_EXTENSIONS['erasure_boundary']
    ]
IGNORE_REGEX = f'({"|".join(IGNORE)})*'


def clean_word(word: str) -> str:
    return re.sub(IGNORE_REGEX, '', word)
