from collections.abc import Mapping, Sequence

NAME_PART_TYPE = "ValueToken"
NAME_BREAK_TYPE = "BrokenAway"

NameToken = Mapping[str, object]


class NonAlternatingName(ValueError):
    pass


def _expected_type(index: int) -> str:
    return NAME_PART_TYPE if index % 2 == 0 else NAME_BREAK_TYPE


def _as_array(name_parts: object) -> Sequence[object]:
    if not isinstance(name_parts, Sequence) or isinstance(name_parts, (str, bytes)):
        raise NonAlternatingName(
            f"Expected nameParts to be an array, found {name_parts!r}. "
            f"There is nothing to split by position; refusing to migrate."
        )
    return name_parts


def _as_token(token: object, index: int) -> NameToken:
    expected = _expected_type(index)
    if not isinstance(token, Mapping) or token.get("type") != expected:
        raise NonAlternatingName(
            f"Expected a {expected} at position {index} of nameParts, "
            f"found {token!r}. Splitting by position would move it into "
            f"the wrong array; refusing to migrate."
        )
    return token


def _validate_ends_with_a_part(tokens: Sequence[NameToken]) -> None:
    if len(tokens) % 2 == 0:
        raise NonAlternatingName(
            f"Expected nameParts to start and end with a {NAME_PART_TYPE}, "
            f"found {len(tokens)} tokens. No name the parser writes has that "
            f"shape; refusing to migrate."
        )


def separate_name_parts(
    name_parts: object,
) -> tuple[list[NameToken], list[NameToken]]:
    tokens = [
        _as_token(token, index) for index, token in enumerate(_as_array(name_parts))
    ]
    _validate_ends_with_a_part(tokens)
    return tokens[0::2], tokens[1::2]
