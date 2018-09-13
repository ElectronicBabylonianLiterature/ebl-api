import re
import pydash


def create_query(signs):
    sign_separator = ' '

    lines_regexp = (
        pydash.chain(signs)
        .map(lambda row: [re.escape(sign) for sign in row])
        .map(sign_separator.join)
        .map(lambda row: fr'(?<![^ |\n]){row}')
        .join(r'( .*)?\n.*')
        .value()
    )

    return fr'{lines_regexp}(?![^ |\n])'
