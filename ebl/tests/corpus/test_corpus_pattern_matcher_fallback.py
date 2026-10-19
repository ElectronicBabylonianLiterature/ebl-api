from ebl.corpus.infrastructure.corpus_search_aggregations import CorpusPatternMatcher

EMPTY_PROJECTION = {
    "$project": {
        "textId": True,
        "stage": True,
        "name": True,
        "lines": [],
        "variants": [],
        "matchCount": {"$literal": 0},
    }
}


def test_a_query_with_neither_lemmas_nor_transliteration_matches_nothing() -> None:
    pipeline = CorpusPatternMatcher({"textId": "L.1"}).build_pipeline()

    assert pipeline[0] == EMPTY_PROJECTION


def test_the_empty_pipeline_still_gets_the_result_wrapper() -> None:
    pipeline = CorpusPatternMatcher({}).build_pipeline()

    assert pipeline[0] == EMPTY_PROJECTION
    assert len(pipeline) > 1


def test_a_transliteration_query_does_not_use_the_empty_projection() -> None:
    pipeline = CorpusPatternMatcher({"transliteration": [["KU"]]}).build_pipeline()

    assert pipeline[0] != EMPTY_PROJECTION


def test_a_lemma_query_does_not_use_the_empty_projection() -> None:
    pipeline = CorpusPatternMatcher({"lemmas": ["ana I"]}).build_pipeline()

    assert pipeline[0] != EMPTY_PROJECTION
