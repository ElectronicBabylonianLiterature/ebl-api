import pytest
from ebl.fragmentarium.application.fragment_fields_schemas import ScriptSchema
from ebl.fragmentarium.domain.fragment import Script
from ebl.common.domain.period import Period, PeriodModifier


@pytest.mark.parametrize(
    "script,serialized",
    [
        (
            Script(Period.FARA, PeriodModifier.EARLY, True),
            {
                "period": "Fara",
                "periodModifier": "Early",
                "uncertain": True,
                "sortKey": Period.FARA.sort_key,
            },
        ),
        (
            Script(),
            {
                "period": "None",
                "periodModifier": "None",
                "uncertain": False,
                "sortKey": 0,
            },
        ),
    ],
)
def test_schema(script, serialized):
    assert ScriptSchema().load(serialized) == script
    assert ScriptSchema().dump(script) == serialized
