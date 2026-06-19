import pytest

from ebl.bibliography.application.duplicate_audit import normalize_entry, score_pair
from ebl.tests.bibliography.duplicate_audit_test_helpers import (
    entry,
    score_entries,
    score_entries_with_shared_overrides,
)


def test_book_series_part_siblings_are_not_likely_duplicates() -> None:
    left = normalize_entry(
        entry(
            "A",
            title="Cuneiform Texts Part I",
            **{"collection-title": "Cuneiform Texts", "volume": "1"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            title="Cuneiform Texts Part II",
            **{"collection-title": "Cuneiform Texts", "volume": "2"},
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert "series_part" in score.conflicting_signals


@pytest.mark.parametrize(
    ("shared_overrides", "left_title", "right_title", "conflict"),
    [
        (
            {
                "author": [{"family": "Smith", "given": "Mark"}],
                "issued": {"date-parts": [[2010]]},
                "publisher": "Eisenbrauns",
                "collection-title": "Babylonian Provincial Officials",
            },
            "Babylonian Provincial Officials Part One",
            "Babylonian Provincial Officials Part Two",
            "series_part",
        ),
        (
            {
                "author": [{"family": "Jones", "given": "Mary"}],
                "issued": {"date-parts": [[1971]]},
                "publisher": "University Museum",
                "collection-title": "Babylonian Publications Series",
            },
            "Administrative Documents from Ur",
            "Sumerian Literary Catalogues",
            "different_title",
        ),
    ],
)
def test_title_only_book_variants_are_not_duplicates(
    shared_overrides, left_title, right_title, conflict
) -> None:
    score = score_entries_with_shared_overrides(
        shared_overrides,
        {"title": left_title},
        {"title": right_title},
    )
    assert score.decision == "not_duplicate"
    assert conflict in score.conflicting_signals


@pytest.mark.parametrize(
    ("left_overrides", "right_overrides"),
    [
        (
            {"title": "Royal Archives Volume I", "volume": "1"},
            {"title": "Royal Archives Volume II", "volume": "2"},
        ),
        (
            {"title": "Urkunden aus Lagasch Teil 1"},
            {"title": "Urkunden aus Lagasch Teil 2"},
        ),
        (
            {"title": "Archiv fur Orientforschung Band I Heft 1"},
            {"title": "Archiv fur Orientforschung Band I Heft 2"},
        ),
    ],
)
def test_book_series_siblings_are_not_likely_duplicates(
    left_overrides, right_overrides
) -> None:
    score = score_entries(left_overrides, right_overrides)
    assert score.decision != "likely_duplicate"
    assert "series_part" in score.conflicting_signals


def test_encyclopedia_entries_need_high_title_similarity() -> None:
    score = score_entries(
        {
            "type": "entry-encyclopedia",
            "title": "Adad",
            "container-title": "Reallexikon der Assyriologie",
            "volume": "1",
        },
        {
            "type": "entry-encyclopedia",
            "title": "Ea",
            "container-title": "Reallexikon der Assyriologie",
            "volume": "1",
        },
    )
    assert score.decision == "not_duplicate"
    assert "different_entry_title" in score.conflicting_signals


def test_same_encyclopedia_lemma_remains_likely_duplicate() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="entry-encyclopedia",
            title="Marduk",
            issued={"date-parts": [[1999]]},
            page="360-370",
            **{"container-title": "Reallexikon der Assyriologie", "volume": "7"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="entry-encyclopedia",
            title="Marduk.",
            issued={"date-parts": [[1999]]},
            page="360-370",
            **{"container-title": "Reallexikon der Assyriologie", "volume": "7"},
        )
    )
    score = score_pair(left, right)
    assert score.decision == "likely_duplicate"


def test_encyclopedia_distinct_lemmas_are_not_likely_duplicate() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="entry-encyclopedia",
            title="Zelt A. I. Philologisch. In Mesopotamien · Tent A. I. Philological. In Mesopotamia",
            issued={"date-parts": [[2017]]},
            **{"container-title": "Reallexikon der Assyriologie", "volume": "15"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="entry-encyclopedia",
            title="Wasser A. I. Philologisch. In Mesopotamien · Water A. I. Philological. In Mesopotamia",
            issued={"date-parts": [[2017]]},
            **{"container-title": "Reallexikon der Assyriologie", "volume": "15"},
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert "different_entry_title" in score.conflicting_signals


def test_webpage_stt_siblings_are_not_likely_duplicate() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="webpage",
            title="STT 1, 061 [Šu'ila to Šamaš]. (http://oracc.org/cams/gkab/P338379)",
            issued={"date-parts": [[2009]]},
            author=[{"family": "Cunningham", "given": "Graham"}],
            **{"container-title": "CAMS/GKAB"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="webpage",
            title="STT 2, 122 [Šu'ila to Šamaš]. (http://oracc.org/cams/gkab/P338442)",
            issued={"date-parts": [[2009]]},
            author=[{"family": "Cunningham", "given": "Graham"}],
            **{"container-title": "CAMS/GKAB"},
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"


def test_implicit_series_part_sibling_is_not_likely_duplicate() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="article-journal",
            title="Neue babylonische Planeten-Tafeln II",
            issued={"date-parts": [[1891]]},
            DOI="10.1000/shared",
            **{"container-title": "Zeitschrift für Assyriologie", "volume": "6"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="article-journal",
            title="Neue babylonische Planeten-Tafeln",
            issued={"date-parts": [[1891]]},
            DOI="10.1000/shared",
            **{"container-title": "Zeitschrift für Assyriologie", "volume": "6"},
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
    assert (
        "series_part" in score.conflicting_signals
        or "doi_data_issue" in score.conflicting_signals
    )


def test_complete_incomplete_dates_are_not_likely_duplicate() -> None:
    left = normalize_entry(
        entry(
            "A",
            type="book",
            title=(
                "Documents From the Temple Archives of Nippur, "
                "Dated in the Reigns of Cassite Rulers (Incomplete Dates)"
            ),
            issued={"date-parts": [[1906]]},
            publisher="University Museum",
            **{"container-title": "BE", "collection-title": "BE"},
        )
    )
    right = normalize_entry(
        entry(
            "B",
            type="book",
            title=(
                "Documents From the Temple Archives of Nippur, "
                "Dated in the Reigns of Cassite Rulers (Complete Dates)"
            ),
            issued={"date-parts": [[1906]]},
            publisher="University Museum",
            **{"container-title": "BE", "collection-title": "BE"},
        )
    )
    score = score_pair(left, right)
    assert score.decision != "likely_duplicate"
