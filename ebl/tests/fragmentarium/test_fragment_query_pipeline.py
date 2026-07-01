from ebl.fragmentarium.infrastructure.fragment_pattern_matcher import PatternMatcher


def test_pagination_stages_are_applied_in_order():
    pipeline = PatternMatcher(
        {"offset": 10, "limit": 5}, provenance_service=None
    ).build_pipeline()

    pagination_facet = next(stage["$facet"] for stage in pipeline if "$facet" in stage)
    summary_projection = pipeline[-1]["$project"]

    assert pagination_facet["items"][1:3] == [{"$skip": 10}, {"$limit": 5}]
    assert pagination_facet["metadata"] == [
        {
            "$group": {
                "_id": None,
                "totalCount": {"$sum": 1},
                "matchCountTotal": {"$sum": "$matchCount"},
            }
        }
    ]
    assert summary_projection["matchCountTotal"] == {
        "$ifNull": [{"$arrayElemAt": ["$metadata.matchCountTotal", 0]}, 0]
    }
    assert summary_projection["totalCount"] == {
        "$ifNull": [{"$arrayElemAt": ["$metadata.totalCount", 0]}, 0]
    }


def test_pipeline_without_pagination_keeps_all_items():
    pipeline = PatternMatcher(
        {"number": "K.*"}, provenance_service=None
    ).build_pipeline()

    pagination_facet = next(stage["$facet"] for stage in pipeline if "$facet" in stage)

    assert not any(
        "$skip" in stage or "$limit" in stage for stage in pagination_facet["items"]
    )
