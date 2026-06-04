from ebl.common.query.query_result import LemmaQueryType
from ebl.corpus.infrastructure.corpus_lemma_matcher import CorpusLemmaMatcher


def test_create_chapter_prefilter_for_or_query_type() -> None:
    matcher = CorpusLemmaMatcher(["lemma-a", "lemma-b"], LemmaQueryType.OR)

    assert matcher._create_chapter_prefilter() == {
        "$or": [
            {
                "lines.variants.reconstruction.uniqueLemma": {
                    "$in": ["lemma-a", "lemma-b"]
                }
            },
            {
                "lines.variants.manuscripts.line.content.uniqueLemma": {
                    "$in": ["lemma-a", "lemma-b"]
                }
            },
        ]
    }


def test_create_chapter_prefilter_for_and_query_type() -> None:
    matcher = CorpusLemmaMatcher(["lemma-a", "lemma-b"], LemmaQueryType.AND)

    assert matcher._create_chapter_prefilter() == {
        "$and": [
            {
                "$or": [
                    {"lines.variants.reconstruction.uniqueLemma": "lemma-a"},
                    {"lines.variants.manuscripts.line.content.uniqueLemma": "lemma-a"},
                ]
            },
            {
                "$or": [
                    {"lines.variants.reconstruction.uniqueLemma": "lemma-b"},
                    {"lines.variants.manuscripts.line.content.uniqueLemma": "lemma-b"},
                ]
            },
        ]
    }


def test_line_query_omits_match_count_when_disabled() -> None:
    matcher = CorpusLemmaMatcher(["lemma-a"], LemmaQueryType.LINE)

    pipeline = matcher.build_pipeline(count_matches_per_item=False)

    assert "matchCount" not in pipeline[-2]["$group"]
    assert "matchCount" not in pipeline[-1]["$project"]


def test_line_query_includes_match_count_when_enabled() -> None:
    matcher = CorpusLemmaMatcher(["lemma-a"], LemmaQueryType.LINE)

    pipeline = matcher.build_pipeline(count_matches_per_item=True)

    assert pipeline[-2]["$group"]["matchCount"] == {"$sum": 1}
    assert pipeline[-1]["$project"]["matchCount"] is True
