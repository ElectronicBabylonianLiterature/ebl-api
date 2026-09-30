from typing import Any, cast

from ebl.common.domain.period import Period
from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQueryArchaeologySchema,
    FragmentQuerySummarySchema,
    deserialize_script_period,
)
from ebl.fragmentarium.domain.fragment_query_summary import (
    FragmentQueryArchaeology,
    FragmentQuerySummary,
    empty_matching_line_preview,
)
from ebl.tests.fragmentarium.test_fragment_query_summary_schema import build_summary


def test_fragment_query_script_period_accepts_a_long_name():
    assert deserialize_script_period("Neo-Assyrian") is Period.NEO_ASSYRIAN


def test_fragment_query_archaeology_schema_loads_an_empty_site_as_none():
    archaeology = cast(
        FragmentQueryArchaeology,
        FragmentQueryArchaeologySchema().load({"site": {}}),
    )

    assert archaeology.site is None


def test_fragment_query_summary_schema_defaults_an_absent_preview():
    dumped = cast(dict[str, Any], FragmentQuerySummarySchema().dump(build_summary()))
    del dumped["matchingLinePreview"]

    loaded = cast(FragmentQuerySummary, FragmentQuerySummarySchema().load(dumped))

    assert loaded.matching_line_preview == empty_matching_line_preview()
