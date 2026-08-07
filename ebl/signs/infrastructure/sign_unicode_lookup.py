from typing import Dict, Iterable, List, Tuple

from ebl.mongo_collection import MongoCollection
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.enclosure_tokens import Determinative

WHITESPACE = "whitespace"
WHITESPACE_UNICODE = 9999


def extract_word_sub_indexes(word) -> Iterable[Tuple[str, int]]:
    for part in word._parts:
        if isinstance(part, Determinative):
            part = part._parts[0]
        if getattr(part, "name_parts", []):
            yield (part.name_parts[0].name_contribution, part.sub_index)
    yield (WHITESPACE, 1)


def extract_words_sub_indexes(result) -> Iterable[Tuple[str, int]]:
    return (
        value_index
        for line in result.lines
        for word in line._content
        for value_index in extract_word_sub_indexes(word)
    )


def find_unicode(
    collection: MongoCollection, values_indexes: Iterable[Tuple[str, int]]
) -> Iterable[Dict[str, List[int]]]:
    for value, sub_index in values_indexes:
        if value == WHITESPACE:
            yield {"unicode": [WHITESPACE_UNICODE]}
        else:
            query = {"values": {"$elemMatch": {"value": value, "subIndex": sub_index}}}
            yield from collection.find_many(query, {"_id": 0, "unicode": 1})


def get_unicode_from_atf(
    collection: MongoCollection, line: str
) -> List[Dict[str, List[int]]]:
    text = parse_atf_lark(f"1. {line}")
    values_indexes = extract_words_sub_indexes(text)
    return list(find_unicode(collection, values_indexes))[:-1]
