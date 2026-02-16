import pytest
from ebl.transliteration.infrastructure.queries import build_query


PATH_PREFIX = "someNumber"


def create_dto(prefix, number, suffix) -> dict:
    dto = {
        "prefix": prefix,
        "number": number,
        "suffix": suffix,
    }
    return {key: value for key, value in dto.items() if value is not None}


def add_path_prefix(dto: dict):
    return {f"{PATH_PREFIX}.{key}": value for key, value in dto.items()}


PREFIXES = ["X", "", "*"]
NUMBERS = ["123", "", "*"]
SUFFIXES = ["a", "", "*"]
WILDCARDS = [True, False]


@pytest.mark.parametrize("prefix", PREFIXES)
@pytest.mark.parametrize("number", NUMBERS)
@pytest.mark.parametrize("suffix", SUFFIXES)
@pytest.mark.parametrize("wildcard", WILDCARDS)
def test_build_query(prefix, number, suffix, wildcard):
    suffix = "*" if wildcard and number == "*" and not suffix else suffix
    data = (prefix, number, suffix)
    dto = create_dto(*data)
    expected = add_path_prefix(
        create_dto(*(None if wildcard and value == "*" else value for value in data))
    )
    assert build_query(PATH_PREFIX, dto, wildcard) == expected
