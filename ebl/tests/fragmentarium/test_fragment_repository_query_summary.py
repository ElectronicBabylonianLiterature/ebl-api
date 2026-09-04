from typing import cast

import pytest

from ebl.errors import NotFoundError
from ebl.fragmentarium.application.fragment_query_summary_schema import (
    FragmentQueryResultSchema,
)
from ebl.fragmentarium.domain.fragment import Script
from ebl.fragmentarium.domain.fragment_query_summary import FragmentQueryResult


def test_query_fragmentarium_limit_summary_missing_hydration_fails_clearly(
    fragment_repository,
):
    with pytest.raises(NotFoundError, match="Fragment summary data"):
        fragment_repository._load_fragment_query_result(
            {
                "items": [
                    {
                        "_id": "missing",
                        "museumNumber": {"prefix": "K", "number": "1", "suffix": ""},
                        "matchingLines": [],
                        "matchCount": 0,
                    }
                ],
                "matchCountTotal": 0,
            }
        )


def test_query_fragmentarium_limit_summary_hydration_uses_safe_defaults(
    fragment_repository,
):
    result = cast(
        FragmentQueryResult,
        FragmentQueryResultSchema().load(
            {
                "items": [
                    fragment_repository._hydrate_fragment_query_item(
                        {
                            "_id": "K.1",
                            "museumNumber": {
                                "prefix": "K",
                                "number": "1",
                                "suffix": "",
                            },
                            "matchingLines": [0, 1],
                        },
                        {
                            "K.1": {
                                "museumNumber": {
                                    "prefix": "K",
                                    "number": "1",
                                    "suffix": "",
                                },
                                "text": {"lines": [{"prefix": "1.", "content": []}]},
                            }
                        },
                        (),
                    )
                ],
                "matchCountTotal": 0,
            }
        ),
    )

    summary = result.items[0]
    assert summary.description == ""
    assert summary.script == Script()
    assert len(summary.matching_line_preview["lines"]) == 1


def test_query_fragmentarium_limit_summary_missing_museum_number_fails_clearly(
    fragment_repository,
):
    with pytest.raises(NotFoundError, match="Fragment summary data"):
        fragment_repository._hydrate_fragment_query_item(
            {"_id": "K.1", "matchingLines": []}, {"K.1": {"text": {"lines": []}}}, ()
        )
