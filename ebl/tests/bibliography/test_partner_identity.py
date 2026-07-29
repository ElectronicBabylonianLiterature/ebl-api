import pytest

from ebl.bibliography.application.partner_identity import (
    MAX_CITATION_KEY_SUFFIX,
    create_partner_alias,
    generate_partner_citation_key,
)
from ebl.errors import DataError, DuplicateError


def test_create_partner_alias_rejects_empty_normalized_id():
    with pytest.raises(DataError, match="letter or digit"):
        create_partner_alias("!!!")


def test_generate_partner_citation_key_returns_none_without_meaningful_data():
    entry = {"id": "Q30000000", "type": "book", "title": "Missing creator and year"}

    assert generate_partner_citation_key(entry, lambda _value: False) is None


def test_generate_partner_citation_key_raises_duplicate_when_candidates_exhausted():
    base_key = "miccadei2002Synergistic"
    unavailable = {base_key, *(f"{base_key}-{suffix}" for suffix in range(2, 101))}
    entry = {
        "type": "article-journal",
        "title": "The Synergistic Activity of Thyroid Transcription Factor 1",
        "author": [{"given": "Stefania", "family": "Miccadei"}],
        "issued": {"date-parts": [[2002, 1, 1]]},
    }
    checked_values = []

    def lookup_value_exists(value):
        checked_values.append(value)
        return value in unavailable

    with pytest.raises(
        DuplicateError, match="Unable to generate a unique citation key"
    ):
        generate_partner_citation_key(entry, lookup_value_exists)

    assert len(checked_values) == MAX_CITATION_KEY_SUFFIX
    assert checked_values[0] == base_key
    assert checked_values[-1] == f"{base_key}-{MAX_CITATION_KEY_SUFFIX}"
