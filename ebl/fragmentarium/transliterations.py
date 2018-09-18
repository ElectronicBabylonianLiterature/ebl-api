import re
import pydash


def clean(transliteration):
    return (pydash
            .chain(transliteration)
            .thru(filter_lines)
            .map(lambda line: re.sub(r'^[^\.]+\.([^\.]+\.)?\s+|'
                                     r'<<?\(?[^>]+\)?>?>|'
                                     r'\[\(?|'
                                     r'\)?\]|'
                                     r'\.\.\.', '', line))
            .map(lambda line:
                 re.sub(r'\s*{+\+?|}+({+\+?)?\s*|-|\s+\|\s+', ' ', line))
            .map(lambda line:
                 re.sub(r'\(\$_+\$\)|\?|\*|#|!|\$|%\w+\s+', '', line))
            .map(lambda line: re.sub(r'(?<=\s)\(([^\(\)]+)\)', r'\1', line))
            .map(pydash.clean)
            .map(lambda line: line.split(' '))
            .map(lambda line: [
                _clean_value(value)
                for value in line
            ])
            .map(' '.join)
            .value())


def _clean_value(value):
    match = re.fullmatch(r'\|[^|]+\|', value)
    if match:
        return value
    else:
        return re.sub(r'[.+]', ' ', value)


def filter_lines(transliteration):
    return [line
            for line in transliteration.split('\n') if
            line and
            not line.startswith('@') and
            not line.startswith('$') and
            not line.startswith('#') and
            not line.startswith('&') and
            not line.startswith('=:')]
