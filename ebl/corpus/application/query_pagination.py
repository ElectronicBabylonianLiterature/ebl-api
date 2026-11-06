from typing import Dict

from ebl.common.query.parameter_parser import (
    parse_limit,
    parse_non_negative_integer_field,
)

DEFAULT_CORPUS_QUERY_LIMIT = 50


def parse_corpus_pagination(parameters: Dict) -> Dict:
    parsed = parse_limit(parse_non_negative_integer_field("offset")(parameters))
    if "offset" in parsed and "limit" not in parsed:
        return {**parsed, "limit": DEFAULT_CORPUS_QUERY_LIMIT}
    return parsed
