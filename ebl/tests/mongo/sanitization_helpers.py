QUERY_SYNTAX_FRAGMENTS = ["{", "}", "$", "_id"]


def assert_no_query_details(message: str) -> None:
    for fragment in QUERY_SYNTAX_FRAGMENTS:
        assert fragment not in message
