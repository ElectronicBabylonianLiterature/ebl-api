import re

from ebl.text.atf import ATF_EXTENSIONS, ATF_SPEC

IGNORE = [
        ATF_SPEC['lacuna']['begin'], # type: ignore
        r'\(',
        r'\)',
        ATF_SPEC['lacuna']['end'], # type: ignore
        ATF_SPEC['flags']['uncertainty'], # type: ignore
        ATF_SPEC['flags']['collation'], # type: ignore
        ATF_SPEC['flags']['damage'], # type: ignore
        ATF_SPEC['flags']['correction'], # type: ignore
        ATF_EXTENSIONS['erasure_illegible'], # type: ignore
        ATF_EXTENSIONS['erasure_boundary'] # type: ignore
    ]
IGNORE_REGEX = f'({"|".join(IGNORE)})*'


def clean_word(word: str) -> str:
    return re.sub(IGNORE_REGEX, '', word)
