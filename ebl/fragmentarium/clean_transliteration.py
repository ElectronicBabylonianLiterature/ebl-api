import re


def clean_transliteration(transliteration):
    return [re.sub(r'(?<=\s)\(([^\(\)]+)\)', r'\1', line).strip()
            for line in
            (re.sub(r'\(\$_+\$\)|\?|\*|#|!|\$|%\w+\s+|(?<=\s)\s', '', line)
             for line in
             (re.sub(r'\s*{+\+?|}+({+\+?)?\s*|-|\.|\s+\|\s+', ' ', line)
              for line in
              (re.sub(r'^[^\.]+\.([^\.]+\.)?\s+|'
                      r'<<?\(?[^>]+\)?>?>|'
                      r'\[\(?|'
                      r'\)?\]|'
                      r'\.\.\.', '', line)
               for line in transliteration.split('\n') if
               line and
               not line.startswith('@') and
               not line.startswith('$') and
               not line.startswith('#') and
               not line.startswith('&') and
               not line.startswith('=:'))))]