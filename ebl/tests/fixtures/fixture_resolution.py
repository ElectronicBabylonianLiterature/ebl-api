from typing import Any, Dict, Mapping

import pytest


def resolve_fixtures(
    request: pytest.FixtureRequest, fixtures: Mapping[str, str]
) -> Dict[str, Any]:
    return {
        argument: request.getfixturevalue(fixture)
        for argument, fixture in fixtures.items()
    }
