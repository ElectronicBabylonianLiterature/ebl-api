from pyoracc.atf.common.atffile import AtfFile


ATF_HEADING = [
    '&XXX = XXX',
    '#project: eblo',
    '#atf: lang akk-x-stdbab',
    '#atf: use unicode',
    '#atf: use math',
    '#atf: use legacy'
]


class AtfError(Exception):
    pass


class AtfSyntaxError(AtfError):
    def __init__(self, source):
        self.lineno = source.lineno - len(ATF_HEADING)
        self.text = source.text
        super().__init__(f"Invalid token '{self.text}' at line {self.lineno}.")


def validate_atf(text):
    prefix = '\n'.join(ATF_HEADING)
    try:
        AtfFile(f'{prefix}\n{text}', atftype='oracc')
    except SyntaxError as error:
        raise AtfSyntaxError(error)
    except (IndexError,
            AttributeError,
            UnicodeDecodeError) as error:
        raise AtfError(error)
