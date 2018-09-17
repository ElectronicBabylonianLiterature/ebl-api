import re
import pydash


def clean(transliteration):
    return [pydash.clean(re.sub(r'(?<=\s)\(([^\(\)]+)\)', r'\1', line))
            for line in
            (re.sub(r'\(\$_+\$\)|\?|\*|#|!|\$|%\w+\s+', '', line)
             for line in
             (re.sub(r'\s*{+\+?|}+({+\+?)?\s*|-|\.|\s+\|\s+', ' ', line)
              for line in
              (re.sub(r'^[^\.]+\.([^\.]+\.)?\s+|'
                      r'<<?\(?[^>]+\)?>?>|'
                      r'\[\(?|'
                      r'\)?\]|'
                      r'\.\.\.', '', line)
               for line in filter_lines(transliteration))))]


def filter_lines(transliteration):
    return [line
            for line in transliteration.split('\n') if
            line and
            not line.startswith('@') and
            not line.startswith('$') and
            not line.startswith('#') and
            not line.startswith('&') and
            not line.startswith('=:')]
