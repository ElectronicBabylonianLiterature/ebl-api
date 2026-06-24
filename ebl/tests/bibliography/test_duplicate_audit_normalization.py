from ebl.bibliography.application.duplicate_audit import (
    normalize_doi,
    normalize_entry,
    normalize_isbn,
    normalize_issn,
    normalize_text,
)
from ebl.tests.bibliography.duplicate_audit_test_helpers import entry


def test_normalize_doi() -> None:
    assert normalize_doi(" DOI: https://doi.org/10.123/ABC ") == "10.123/abc"
    assert normalize_doi("http://dx.doi.org/10.1000/X") == "10.1000/x"
    assert normalize_doi("") == ""
    assert normalize_doi("<>") == ""
    assert normalize_doi("pending") == ""


def test_normalize_isbn() -> None:
    assert normalize_isbn("978-0-19-927841-1") == "9780199278411"
    assert normalize_isbn("0 306 40615 X") == "030640615X"


def test_normalize_issn() -> None:
    assert normalize_issn("1234-567X") == "1234567X"


def test_normalize_title() -> None:
    assert normalize_text("L'épopée   de Gilgameš!") == "l epopee de gilgames"


def test_contributor_and_year_normalization() -> None:
    normalized = normalize_entry(entry("A"))
    assert normalized.contributors == ("george|a",)
    assert normalized.primary_family == "george"
    assert normalized.year == 2003
