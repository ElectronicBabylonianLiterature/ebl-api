from ebl.bibliography.application.duplicate_detection import (
    BibliographyDuplicateDetector,
)
from ebl.tests.bibliography.duplicate_detection_test_helpers import (
    FakeBibliographyRepository,
    entry,
)


def test_duplicate_detector_series_sibling_is_not_likely_duplicate() -> None:
    detector = BibliographyDuplicateDetector(
        FakeBibliographyRepository(
            [
                entry(
                    "Q30000000",
                    DOI="",
                    title="Babylonian Provincial Officials Part One",
                    volume="1",
                )
            ]
        )
    )

    result = detector.find_candidates(
        entry(
            "Q30000001",
            DOI="",
            title="Babylonian Provincial Officials Part Two",
            volume="2",
        )
    ).to_dict()

    assert result["decision"] == "no_duplicate"
    assert result["candidates"][0]["decision"] == "no_duplicate"
    assert "series_part" in result["candidates"][0]["conflictingFields"]


def test_duplicate_detector_placeholder_doi_does_not_match_identifier() -> None:
    detector = BibliographyDuplicateDetector(
        FakeBibliographyRepository(
            [
                entry(
                    "Q30000000",
                    DOI="<>",
                    title="Different Article",
                    page="800-820",
                )
            ]
        )
    )

    result = detector.find_candidates(
        entry("Q30000001", DOI="<>", page="837-846")
    ).to_dict()

    assert result["decision"] == "no_duplicate"
    assert result["candidates"][0]["matchedFields"]["doi"] is None


def test_duplicate_detector_valid_doi_with_conflicting_metadata_is_possible() -> None:
    detector = BibliographyDuplicateDetector(
        FakeBibliographyRepository(
            [
                entry(
                    "Q30000000",
                    title="A Grammar of Old Babylonian Letters",
                    author=[{"given": "Jeremy", "family": "Black"}],
                    issued={"date-parts": [[2001, 1, 1]]},
                    page="100-160",
                )
            ]
        )
    )

    result = detector.find_candidates(
        entry(
            "Q30000001",
            title="Administrative Documents from Nippur",
            author=[{"given": "Mary", "family": "Jones"}],
            issued={"date-parts": [[1971, 1, 1]]},
            page="1-50",
        )
    ).to_dict()

    assert result["decision"] == "possible_duplicate"
    assert result["candidates"][0]["decision"] == "possible_duplicate"
    assert "doi_data_issue" in result["candidates"][0]["conflictingFields"]


def test_duplicate_detector_encyclopedia_distinct_lemma_not_likely() -> None:
    detector = BibliographyDuplicateDetector(
        FakeBibliographyRepository(
            [
                entry(
                    "Q30000000",
                    type="entry-encyclopedia",
                    title=(
                        "Wasser A. I. Philologisch. In Mesopotamien · "
                        "Water A. I. Philological. In Mesopotamia"
                    ),
                    DOI="",
                    issued={"date-parts": [[2017]]},
                    **{
                        "container-title": "Reallexikon der Assyriologie",
                        "volume": "15",
                    },
                )
            ]
        )
    )

    result = detector.find_candidates(
        entry(
            "Q30000001",
            type="entry-encyclopedia",
            title=(
                "Zelt A. I. Philologisch. In Mesopotamien · "
                "Tent A. I. Philological. In Mesopotamia"
            ),
            DOI="",
            issued={"date-parts": [[2017]]},
            **{"container-title": "Reallexikon der Assyriologie", "volume": "15"},
        )
    ).to_dict()

    assert result["decision"] != "likely_duplicate"
    assert "different_entry_title" in result["candidates"][0]["conflictingFields"]


def test_duplicate_detector_doi_title_conflict_not_likely() -> None:
    detector = BibliographyDuplicateDetector(
        FakeBibliographyRepository(
            [
                entry(
                    "Q30000000",
                    type="book",
                    title="Sumerian Liturgical Texts",
                    DOI="10.123/SharedDoi",
                    **{
                        "collection-title": "PBS",
                        "container-title": "PBS",
                        "publisher": "University Museum",
                    },
                )
            ]
        )
    )

    result = detector.find_candidates(
        entry(
            "Q30000001",
            type="book",
            title="Sumerian Grammatical Texts",
            DOI="10.123/SharedDoi",
            **{
                "collection-title": "PBS",
                "container-title": "PBS",
                "publisher": "University Museum",
            },
        )
    ).to_dict()

    assert result["decision"] != "likely_duplicate"
    assert result["candidates"][0]["matchedFields"]["doi"] == 1.0
    assert "doi_data_issue" in result["candidates"][0]["conflictingFields"]


def test_duplicate_detector_webpage_sibling_not_likely() -> None:
    detector = BibliographyDuplicateDetector(
        FakeBibliographyRepository(
            [
                entry(
                    "Q30000000",
                    type="webpage",
                    title=(
                        "STT 2, 122 [Šu'ila to Šamaš]. "
                        "(http://oracc.org/cams/gkab/P338442)"
                    ),
                    DOI="",
                    issued={"date-parts": [[2009]]},
                    author=[{"given": "Graham", "family": "Cunningham"}],
                    **{"container-title": "CAMS/GKAB"},
                )
            ]
        )
    )

    result = detector.find_candidates(
        entry(
            "Q30000001",
            type="webpage",
            title=(
                "STT 1, 061 [Šu'ila to Šamaš]. (http://oracc.org/cams/gkab/P338379)"
            ),
            DOI="",
            issued={"date-parts": [[2009]]},
            author=[{"given": "Graham", "family": "Cunningham"}],
            **{"container-title": "CAMS/GKAB"},
        )
    ).to_dict()

    assert result["decision"] != "likely_duplicate"


def test_duplicate_detector_implicit_series_part_not_likely() -> None:
    detector = BibliographyDuplicateDetector(
        FakeBibliographyRepository(
            [
                entry(
                    "Q30000000",
                    type="article-journal",
                    title="Neue babylonische Planeten-Tafeln",
                    DOI="10.1000/shared",
                    issued={"date-parts": [[1891]]},
                    **{
                        "container-title": "Zeitschrift für Assyriologie",
                        "volume": "6",
                    },
                )
            ]
        )
    )

    result = detector.find_candidates(
        entry(
            "Q30000001",
            type="article-journal",
            title="Neue babylonische Planeten-Tafeln II",
            DOI="10.1000/shared",
            issued={"date-parts": [[1891]]},
            **{
                "container-title": "Zeitschrift für Assyriologie",
                "volume": "6",
            },
        )
    ).to_dict()

    assert result["decision"] != "likely_duplicate"
