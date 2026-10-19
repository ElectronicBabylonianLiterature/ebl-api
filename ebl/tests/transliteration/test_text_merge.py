import pytest
from ebl.tests.transliteration.text_merge_cases_1 import TEXT_MERGE_CASES_1
from ebl.tests.transliteration.text_merge_cases_2 import TEXT_MERGE_CASES_2

from ebl.transliteration.domain.text import Text


@pytest.mark.parametrize(
    "old,new,expected",
    [
        *TEXT_MERGE_CASES_1,
        *TEXT_MERGE_CASES_2,
    ],
)
def test_merge(old: Text, new: Text, expected: Text) -> None:
    new_version = f"{old.parser_version}-test"
    merged = old.merge(new.set_parser_version(new_version))
    assert merged == expected.set_parser_version(new_version)
