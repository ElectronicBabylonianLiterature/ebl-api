import re


def clean_transliteration(transliteration):
    return [re.sub(r'[^\s]*\[.*?\][^\s]*|\(\$_+\$\)', '', line).strip()
            for line in
            (re.sub(r'{\+?|}{?\+?|-|\.|\s{2,}', ' ', line)
             for line in
             (re.sub(r'^\d+.?\.\s+(%\w+\s+)?', '', line)
              for line in transliteration.split('\n') if
              line and
              not line.startswith('@') and
              not line.startswith('$') and
              not line.startswith('#')))]
