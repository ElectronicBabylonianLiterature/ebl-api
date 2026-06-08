from ebl.bibliography.application.duplicate_detection import BibliographyDuplicateDetector


class FakeBibliographyRepository:
    def __init__(self, candidates):
        self._candidates = candidates

    def query_duplicate_candidates(self, _entry, _limit):
        return self._candidates


def entry(id_, **overrides):
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


def test_duplicate_detector_no_candidates() -> None:
    detector = BibliographyDuplicateDetector(FakeBibliographyRepository([]))

    result = detector.find_candidates(entry("Q30000001")).to_dict()

    assert result["decision"] == "no_duplicate"
    assert result["highestScore"] == 0.0
    assert result["candidates"] == []
