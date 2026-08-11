from typing import Dict, Iterable, List, Optional, Tuple

from ebl.mongo_collection import MongoCollection
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark
from ebl.transliteration.domain.enclosure_tokens import Determinative
from ebl.transliteration.domain.sign_tokens import NamedSign
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.tokens import Token

WHITESPACE = "whitespace"
WHITESPACE_UNICODE = 9999

ValueSubIndex = Tuple[str, Optional[int]]


def extract_word_sub_indexes(word: Token) -> Iterable[ValueSubIndex]:
    for part in word.parts:
        sign = part.parts[0] if isinstance(part, Determinative) else part
        if isinstance(sign, NamedSign) and sign.name_parts:
            yield (sign.name_parts[0].name_contribution, sign.sub_index)
    yield (WHITESPACE, 1)


def extract_words_sub_indexes(text: Text) -> Iterable[ValueSubIndex]:
    return (
        value_index
        for line in text.lines
        if isinstance(line, TextLine)
        for word in line.content
        for value_index in extract_word_sub_indexes(word)
    )


def find_unicode(
    collection: MongoCollection, values_indexes: Iterable[ValueSubIndex]
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
