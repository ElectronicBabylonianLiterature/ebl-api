def create_query(signs):
    sign_separator = ' '
    line_regexps = [
        fr'(?<![^ |\n]){sign_separator.join(row)}'
        for row in signs
    ]
    lines_regexp = r'( .*)?\n.*'.join(line_regexps)
    return fr'{lines_regexp}(?![^ |\n])'
