from ebl.fragmentarium.infrastructure.fragment_pattern_matcher import PatternMatcher
from ebl.fragmentarium.infrastructure.fragment_sign_matcher import SignMatcher


def _items_facet(pipeline):
    return next(stage["$facet"]["items"] for stage in pipeline if "$facet" in stage)


def _count_facet(pipeline):
    return next(stage["$facet"]["count"] for stage in pipeline if "$facet" in stage)


def _facet(pipeline):
    return next(stage["$facet"] for stage in pipeline if "$facet" in stage)


def _result_projection(pipeline):
    return next(
        stage["$project"] for stage in reversed(pipeline) if "$project" in stage
    )


def _contains_key(value, key):
    if isinstance(value, dict):
        return key in value or any(_contains_key(item, key) for item in value.values())
    if isinstance(value, list):
        return any(_contains_key(item, key) for item in value)
    return False


def test_sign_matcher_prefilters_fragments_before_mapping_lines():
    pattern = [r"(?<![^|\s])kur₂(?![^\s\/])"]

    pipeline = SignMatcher(pattern).build_pipeline()

    assert pipeline[0] == {"$match": {"$and": [{"signs": {"$regex": pattern[0]}}]}}
    assert "$project" in pipeline[1]
    assert pipeline[1]["$project"] == {
        "museumNumber": True,
        "_sortKey": True,
        "_scriptSortKey": "$script.sortKey",
        "lineTypes": "$text.lines.type",
        "signs": True,
    }


def test_fragment_query_summary_phase_one_has_no_lookup_or_hydration():
    items = _items_facet(
        PatternMatcher(
            {"transliteration": ["kur₂"], "limit": 10}, None
        ).build_pipeline()
    )

    assert items == [
        {"$sort": {"_scriptSortKey": 1, "_sortKey": 1}},
        {"$limit": 10},
        {
            "$project": {
                "_id": True,
                "matchCount": True,
                "matchingLines": True,
                "museumNumber": True,
            }
        },
    ]
    assert not any("$lookup" in stage for stage in items)
    assert not _contains_key(items, "$expr")
    assert not _contains_key(items, "matchingLinePreview")


def test_fragment_query_applies_limit_before_phase_one_projection():
    items = _items_facet(
        PatternMatcher(
            {"transliteration": ["kur₂"], "limit": 10}, None
        ).build_pipeline()
    )

    assert items.index({"$limit": 10}) < len(items) - 1


def test_fragment_query_applies_offset_before_limit_and_phase_one_projection():
    items = _items_facet(
        PatternMatcher(
            {"transliteration": ["kur₂"], "limit": 10, "offset": 5}, None
        ).build_pipeline()
    )

    assert items.index({"$skip": 5}) < items.index({"$limit": 10}) < len(items) - 1


def test_fragment_query_without_limit_uses_lean_items():
    items = _items_facet(
        PatternMatcher({"transliteration": ["kur₂"]}, None).build_pipeline()
    )

    assert not any("$limit" in stage for stage in items)
    assert not any("$lookup" in stage for stage in items)
    assert items[-1] == {
        "$project": {
            "_id": False,
            "museumNumber": True,
            "matchingLines": True,
            "matchCount": True,
        }
    }


def test_fragment_query_count_facet_stays_lightweight():
    pipeline = PatternMatcher({"transliteration": ["kur₂"]}, None).build_pipeline()
    count = _count_facet(pipeline)

    assert count == [
        {
            "$group": {
                "_id": None,
                "matchCountTotal": {"$sum": {"$ifNull": ["$matchCount", 0]}},
            }
        },
        {"$project": {"_id": False, "matchCountTotal": True}},
    ]
    assert _result_projection(pipeline) == {
        "_id": False,
        "items": True,
        "matchCountTotal": {
            "$ifNull": [{"$arrayElemAt": ["$count.matchCountTotal", 0]}, 0]
        },
        "isMatchCountTotalExact": {"$literal": True},
        "hasNextPage": {"$literal": None},
    }


def test_fragment_query_count_none_omits_exact_count_facet():
    pipeline = PatternMatcher(
        {"transliteration": ["kur₂"], "limit": 10, "count": "none"}, None
    ).build_pipeline()

    assert "count" not in _facet(pipeline)
    assert _result_projection(pipeline) == {
        "_id": False,
        "items": True,
        "matchCountTotal": {"$literal": None},
        "isMatchCountTotalExact": {"$literal": False},
        "hasNextPage": {"$literal": None},
    }


def test_fragment_query_count_page_fetches_sentinel_and_slices_items():
    pipeline = PatternMatcher(
        {"transliteration": ["kur₂"], "limit": 10, "count": "page"}, None
    ).build_pipeline()
    items = _items_facet(pipeline)

    assert "count" not in _facet(pipeline)
    assert {"$limit": 11} in items
    assert {"$limit": 10} not in items
    assert _result_projection(pipeline) == {
        "_id": False,
        "items": {"$slice": ["$items", 10]},
        "matchCountTotal": {"$literal": None},
        "isMatchCountTotalExact": {"$literal": False},
        "hasNextPage": {"$gt": [{"$size": "$items"}, 10]},
    }


def test_fragment_query_count_page_without_limit_has_no_next_page():
    pipeline = PatternMatcher(
        {"transliteration": ["kur₂"], "count": "page"}, None
    ).build_pipeline()

    assert "count" not in _facet(pipeline)
    assert not any("$limit" in stage for stage in _items_facet(pipeline))
    assert _result_projection(pipeline) == {
        "_id": False,
        "items": True,
        "matchCountTotal": {"$literal": None},
        "isMatchCountTotalExact": {"$literal": False},
        "hasNextPage": {"$literal": False},
    }
