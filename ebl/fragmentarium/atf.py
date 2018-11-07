from pyoracc.atf.common.atffile import AtfFile


class AtfError(Exception):
    pass


def validate_atf(text):
    prefix = (
        '&XXX = XXX'
        '#project: eblo'
        '#atf: lang akk-x-stdbab'
        '#atf: use unicode'
        '#atf: use math'
        '#atf: use legacy'
    )

    try:
        AtfFile(f'{prefix}\n{text}', atftype='oracc')
    except (SyntaxError,
            IndexError,
            AttributeError,
            UnicodeDecodeError) as error:
        raise AtfError(error)
