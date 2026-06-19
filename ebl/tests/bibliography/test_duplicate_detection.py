from ebl.bibliography.application.duplicate_detection import (
    BibliographyDuplicateDetector,
)
from ebl.tests.bibliography.duplicate_detection_test_helpers import (
    FakeBibliographyRepository,
    entry,
)


def test_duplicate_detector_response_shape() -> None:
    detector = BibliographyDuplicateDetector(
        FakeBibliographyRepository([entry("Q30000000")])
    )

    result = detector.find_candidates(entry("Q30000001")).to_dict()

    assert result["decision"] == "likely_duplicate"
    assert result["highestScore"] >= 0.92
    assert result["candidates"][0]["id"] == "Q30000000"
    assert result["candidates"][0]["citationKey"] is None
    assert result["candidates"][0]["recommendation"] == "block_or_request_override"
    assert result["candidates"][0]["matchedFields"]["doi"] == 1.0


def test_duplicate_detector_possible_duplicate_response() -> None:
    detector = BibliographyDuplicateDetector(
        FakeBibliographyRepository(
            [entry("Q30000000", issued={"date-parts": [[1999]]})]
        )
    )

    result = detector.find_candidates(entry("Q30000001")).to_dict()

    assert result["decision"] == "possible_duplicate"
    assert result["highestScore"] >= 0.76
    assert result["candidates"][0]["decision"] == "possible_duplicate"
    assert result["candidates"][0]["recommendation"] == "confirm_before_create"


def test_duplicate_detector_insufficient_data_response() -> None:
    detector = BibliographyDuplicateDetector(
        FakeBibliographyRepository(
            [{"id": "Q30000000", "type": "book", "ISSN": "1234-5678"}]
        )
    )

    result = detector.find_candidates(
        {"id": "Q30000001", "type": "book", "ISSN": "12345678"}
    ).to_dict()

    assert result["decision"] == "insufficient_data"
    assert result["candidates"][0]["recommendation"] == "confirm_before_create"


def test_duplicate_detector_no_duplicate_response_with_low_score_candidate() -> None:
    detector = BibliographyDuplicateDetector(
        FakeBibliographyRepository(
            [
                entry(
                    "Q30000000",
                    DOI="",
                    title="Different Article",
                    page="800-820",
                )
            ]
        )
    )

    result = detector.find_candidates(entry("Q30000001")).to_dict()

    assert result["decision"] == "no_duplicate"
    assert result["highestScore"] >= 0.70
    assert result["candidates"][0]["decision"] == "no_duplicate"
    assert result["candidates"][0]["recommendation"] == "allow_create"


def test_duplicate_detector_caps_response_limit() -> None:
    detector = BibliographyDuplicateDetector(
        FakeBibliographyRepository(
            [
                entry(f"Q{index:08}", DOI=f"10.1210/MEND.16.4.{index:04}")
                for index in range(30)
            ]
        )
    )

    result = detector.find_candidates(entry("Q30000001"), limit=999).to_dict()

    assert len(result["candidates"]) == 25


def test_duplicate_detector_no_candidates() -> None:
    detector = BibliographyDuplicateDetector(FakeBibliographyRepository([]))

    result = detector.find_candidates(entry("Q30000001")).to_dict()

    assert result["decision"] == "no_duplicate"
    assert result["highestScore"] == 0.0
    assert result["candidates"] == []
