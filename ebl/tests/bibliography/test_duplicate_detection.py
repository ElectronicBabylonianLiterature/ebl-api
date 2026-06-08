from typing import Any, Optional, Sequence

from ebl.bibliography.application.bibliography_repository import BibliographyRepository
from ebl.bibliography.application.duplicate_detection import (
    BibliographyDuplicateDetector,
)


class FakeBibliographyRepository(BibliographyRepository):
    def __init__(self, candidates: Sequence[dict[str, Any]]):
        self._candidates = candidates

    def create(self, entry: Any) -> str:
        raise NotImplementedError

    def query_by_id(self, id_: str) -> Any:
        raise NotImplementedError

    def query_by_ids(self, ids: Sequence[str]) -> Sequence[Any]:
        raise NotImplementedError

    def update(self, entry: Any) -> None:
        raise NotImplementedError

    def query_by_author_year_and_title(
        self, author: Optional[str], year: Optional[int], title: Optional[str]
    ) -> Sequence[Any]:
        raise NotImplementedError

    def query_by_container_title_and_collection_number(
        self, container_title_short: Optional[str], collection_number: Optional[str]
    ) -> Sequence[Any]:
        raise NotImplementedError

    def query_by_title_short_and_volume(
        self, title_short: Optional[str], volume: Optional[str]
    ) -> Sequence[Any]:
        raise NotImplementedError

    def query_duplicate_candidates(self, entry: Any, limit: int) -> Sequence[Any]:
        return self._candidates

    def query_page(self, after: Optional[str], limit: int) -> Sequence[Any]:
        raise NotImplementedError

    def list_all_bibliography(self) -> Sequence[Any]:
        raise NotImplementedError


def entry(id_: str, **overrides: Any) -> dict[str, Any]:
    data = {
        "id": id_,
        "type": "article-journal",
        "title": "The Synergistic Activity of Thyroid Transcription Factor 1",
        "author": [{"given": "Stefania", "family": "Miccadei"}],
        "issued": {"date-parts": [[2002, 1, 1]]},
        "DOI": "10.1210/MEND.16.4.0808",
        "container-title": "Molecular Endocrinology",
        "volume": "2",
        "issue": "4",
        "page": "837-846",
    }
    data.update(overrides)
    return data


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
