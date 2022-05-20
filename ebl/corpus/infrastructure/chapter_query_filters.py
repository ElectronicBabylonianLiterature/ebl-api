from typing import Tuple, List, Mapping
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


def find_manuscript_matches(query: TransliterationQuery, chapter: Mapping) -> List:
    return [
        (
            chapter["manuscripts"][idx]["id"],
            list(dict.fromkeys(query.match(signs))),
            list(dict.fromkeys(get_line_indexes(chapter, idx))),
        )
        for idx, signs in enumerate(chapter["signs"])
        if query.match(signs)
    ]


def get_line_indexes(chapter: Mapping, idx: int) -> List:
    return [
        lineIdx
        for lineIdx, line in enumerate(chapter["lines"])
        for variant in line["variants"]
        for manuscript in variant["manuscripts"]
        if manuscript["manuscriptId"] == chapter["manuscripts"][idx]["id"]
    ]


def find_chapter_query_lines(
    manuscript_matches: List, chapter_lines: List
) -> Tuple[List, dict]:
    text_lines = []
    colophon_lines_idxs = {}
    for manuscript_id, matches, lines_idxs_in_manuscript in manuscript_matches:
        for match in matches:
            text_lines, colophon_lines_idxs = find_lines_in_range(
                match,
                (manuscript_id, lines_idxs_in_manuscript, chapter_lines),
                text_lines,
                colophon_lines_idxs,
            )
    return text_lines, colophon_lines_idxs


def find_lines_in_range(
    match: tuple,
    lines_info: tuple,
    text_lines: List,
    colophon_lines_idxs: dict,
) -> Tuple[List, dict]:
    start, end = match
    manuscript_id, lines_idxs_in_manuscript, chapter_lines = lines_info
    manuscript_text_lines_length = len(lines_idxs_in_manuscript)
    for manuscript_line_idx in range(start, end + 1):
        text_lines, colophon_lines_idxs = collect_matching_lines(
            (
                manuscript_id,
                manuscript_line_idx,
                manuscript_text_lines_length,
                lines_idxs_in_manuscript,
                chapter_lines,
            ),
            text_lines,
            colophon_lines_idxs,
        )
    return text_lines, colophon_lines_idxs


def collect_matching_lines(
    lines_info: tuple, text_lines: List, colophon_lines_idxs: dict
) -> Tuple[List, dict]:
    (
        manuscript_id,
        manuscript_line_idx,
        manuscript_text_lines_length,
        lines_idxs_in_manuscript,
        chapter_lines,
    ) = lines_info
    if manuscript_line_idx < manuscript_text_lines_length:
        line_idx = lines_idxs_in_manuscript[manuscript_line_idx]
        line = chapter_lines[line_idx]
        if line not in text_lines:
            text_lines.append(line)
    else:
        colophon_lines_idxs.setdefault(str(manuscript_id), []).append(
            manuscript_line_idx - manuscript_text_lines_length
        )
    return text_lines, colophon_lines_idxs
