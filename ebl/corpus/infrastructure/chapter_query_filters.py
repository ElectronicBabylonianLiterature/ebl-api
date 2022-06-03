from typing import Tuple, List, Mapping
from pymongo.collection import Collection
from ebl.transliteration.domain.transliteration_query import TransliterationQuery
from ebl.corpus.domain.chapter_query import ChapterQueryColophonLines


def filter_query_by_transliteration(
    query: TransliterationQuery, cursor: Collection
) -> List:
    _cursor = []
    for chapter in cursor:
        manuscript_matches = find_manuscript_matches(query, chapter)
        text_lines, colophon_lines = find_chapter_query_lines(
            manuscript_matches, chapter["lines"]
        )
        chapter["lines"] = sorted(
            text_lines, key=lambda line: chapter["lines"].index(line)
        )
        chapter["is_filtered_query"] = True
        chapter["colophon_lines_in_query"] = colophon_lines
        #print('!', colophon_lines)
        _cursor.append(chapter)
    return _cursor


def find_manuscript_matches(query: TransliterationQuery, chapter: Mapping) -> List:
    match_indexes = [
        (query.match(signs), idx) for idx, signs in enumerate(chapter["signs"])
    ]
    return [
        (
            chapter["manuscripts"][idx]["id"],
            dict.fromkeys(match),
            list(dict.fromkeys(get_line_indexes(chapter, idx))),
        )
        for match, idx in match_indexes
        if match
    ]


def get_line_indexes(chapter: Mapping, idx: int) -> List:
    return [
        lineIdx
        for lineIdx, line in enumerate(chapter["lines"])
        for variant in line["variants"]
        for manuscript in variant["manuscripts"]
        if manuscript["manuscriptId"] == chapter["manuscripts"][idx]["id"]
        and manuscript["line"]["type"] == "TextLine"
    ]


def find_chapter_query_lines(
    manuscript_matches: List, chapter_lines: List
) -> Tuple[List, Mapping[int, List[int]]]:
    text_lines = []
    colophon_lines = {}
    for manuscript_id, matches, lines_idxs_in_manuscript in manuscript_matches:
        for match in matches:
            text_lines, colophon_lines = find_lines_in_range(
                match,
                (manuscript_id, lines_idxs_in_manuscript, chapter_lines),
                text_lines,
                colophon_lines,
            )
    return text_lines, colophon_lines


def find_lines_in_range(
    match: tuple,
    lines_info: tuple,
    text_lines: List,
    colophon_lines: Mapping[int, List[int]],
) -> Tuple[List, Mapping[int, List[int]]]:
    start, end = match
    manuscript_id, lines_idxs_in_manuscript, chapter_lines = lines_info
    manuscript_text_lines_length = len(lines_idxs_in_manuscript)
    for manuscript_line_idx in range(start, end + 1):
        text_lines, colophon_lines = collect_matching_lines(
            (
                manuscript_id,
                manuscript_line_idx,
                manuscript_text_lines_length,
                lines_idxs_in_manuscript,
                chapter_lines,
            ),
            text_lines,
            colophon_lines,
        )
    return text_lines, colophon_lines


def collect_matching_lines(
    lines_info: tuple, text_lines: List, colophon_lines: Mapping[int, List[int]]
) -> Tuple[List, Mapping[int, List[int]]]:
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
        colophon_lines.setdefault(manuscript_id, []).append(
            manuscript_line_idx - manuscript_text_lines_length
        )
    return text_lines, colophon_lines