from ebl.corpus.infrastructure.corpus_query_result_projection import CORPUS_QUERY_SORT
from ebl.corpus.infrastructure.corpus_search_aggregations import CorpusPatternMatcher


def test_page_materialization_is_bounded_before_the_final_result() -> None:
    pipeline = CorpusPatternMatcher(
        {"lemmas": ["ina I"], "limit": 5, "offset": 10}
    ).build_pipeline()
    facet = next(stage["$facet"] for stage in reversed(pipeline) if "$facet" in stage)
    assert facet["items"] == [
        {"$sort": CORPUS_QUERY_SORT},
        {"$skip": 10},
        {"$limit": 5},
        {"$set": {"name": "$_sortName"}},
        {"$project": {"_id": False, "_sortName": False}},
    ]
    assert all(
        "$skip" not in stage and "$limit" not in stage for stage in facet["count"]
    )
    assert facet["count"] == [
        {
            "$group": {
                "_id": None,
                "totalChapters": {"$sum": 1},
                "matchCountTotal": {"$sum": {"$ifNull": ["$matchCount", 0]}},
            }
        }
    ]
    assert not any("$lookup" in stage for stage in pipeline)


def test_offset_only_pipeline_defaults_to_a_bounded_page() -> None:
    pipeline = CorpusPatternMatcher({"offset": 1}).build_pipeline()
    facet = next(stage["$facet"] for stage in pipeline if "$facet" in stage)
    assert {"$skip": 1} in facet["items"]
    assert {"$limit": 50} in facet["items"]


def test_legacy_unbounded_query_does_not_add_a_pagination_facet() -> None:
    pipeline = CorpusPatternMatcher({"lemmas": ["ina I"]}).build_pipeline()
    assert not any("$facet" in stage for stage in pipeline)
