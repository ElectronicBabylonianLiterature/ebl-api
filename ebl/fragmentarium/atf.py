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
        self.line_number = source.lineno - len(ATF_HEADING)
        self.text = source.text
        message = f"Line {self.line_number} is invalid. Please revise."
        super().__init__(message)


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
