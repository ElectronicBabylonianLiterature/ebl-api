from typing import List
from pymongo.collection import Collection
from ebl.transliteration.domain.transliteration_query import TransliterationQuery


def filter_query_by_transliteration(
    query: TransliterationQuery, cursor: Collection
) -> List:
    _cursor = []
    for chapter in cursor:
        manuscript_matches = find_manuscript_matches(query, chapter)
        text_lines, colophon_lines_idxs = find_chapter_query_lines(
            manuscript_matches, chapter["lines"]
        )
        chapter["lines"] = sorted(text_lines, key=lambda l: chapter["lines"].index(l))
        chapter["is_filtered_query"] = True
        chapter["colophon_lines_in_query"] = colophon_lines_idxs
        _cursor.append(chapter)
    return _cursor


def find_manuscript_matches(query: TransliterationQuery, chapter) -> List:
    return [
        (
            chapter["manuscripts"][idx]["id"],
            list(dict.fromkeys(query.match(signs))),
            [
                lineIdx
                for lineIdx, line in enumerate(chapter["lines"])
                for variant in line["variants"]
                for manuscript in variant["manuscripts"]
                if manuscript["manuscriptId"] == chapter["manuscripts"][idx]["id"]
            ],
        )
        for idx, signs in enumerate(chapter["signs"])
        if query.match(signs)
    ]


def find_chapter_query_lines(
    manuscript_matches: List, chapter_lines: List
) -> (List, dict):
    text_lines = []
    colophon_lines_idxs = {}
    for manuscript_id, matches, lines_idxs_in_manuscript in manuscript_matches:
        manuscript_text_lines_length = len(lines_idxs_in_manuscript)
        for start, end in matches:
            for manuscript_line_idx in range(start, end + 1):
                if manuscript_line_idx < manuscript_text_lines_length:
                    line_idx = lines_idxs_in_manuscript[manuscript_line_idx]
                    line = chapter_lines[line_idx]
                    if line not in text_lines:
                        text_lines.append(line)
                else:
                    colophon_lines_idxs.setdefault(manuscript_id, []).append(
                        manuscript_line_idx - manuscript_text_lines_length
                    )
    return text_lines, colophon_lines_idxs
