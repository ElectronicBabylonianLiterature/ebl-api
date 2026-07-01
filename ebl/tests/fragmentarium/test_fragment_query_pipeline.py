from ebl.fragmentarium.infrastructure.fragment_pattern_matcher import PatternMatcher


def test_pagination_stages_are_applied_in_order():
    pipeline = PatternMatcher(
        {"offset": 10, "limit": 5}, provenance_service=None
    ).build_pipeline()

    pagination_facet = next(stage["$facet"] for stage in pipeline if "$facet" in stage)

    assert pagination_facet["items"][1:3] == [{"$skip": 10}, {"$limit": 5}]
    assert pagination_facet["metadata"] == [{"$count": "totalCount"}]


def test_pipeline_without_pagination_keeps_all_items():
    pipeline = PatternMatcher(
        {"number": "K.*"}, provenance_service=None
    ).build_pipeline()

    pagination_facet = next(stage["$facet"] for stage in pipeline if "$facet" in stage)

    assert not any(
        "$skip" in stage or "$limit" in stage for stage in pagination_facet["items"]
    )
