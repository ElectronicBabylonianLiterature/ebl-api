from pyoracc.atf.common.atffile import AtfFile


class AtfError(Exception):
    pass


def validate_atf(text):
    prefix = (
        '&XXX = XXX\n'
        '#project: eblo\n'
        '#atf: lang akk-x-stdbab\n'
        '#atf: use unicode\n'
        '#atf: use math\n'
        '#atf: use legacy'
    )

    try:
        AtfFile(f'{prefix}\n{text}', atftype='oracc')
    except (SyntaxError,
            IndexError,
            AttributeError,
            UnicodeDecodeError) as error:
        raise AtfError(error)
