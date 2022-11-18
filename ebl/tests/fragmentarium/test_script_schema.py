import pytest
from ebl.fragmentarium.application.fragment_schema import ScriptSchema
from ebl.fragmentarium.domain.fragment import Script
from ebl.common.period import Period, PeriodModifier


@pytest.mark.parametrize(
    "script,serialized",
    [
        (
            Script(Period.FARA, PeriodModifier.EARLY, True),
            {"period": "Fara", "periodModifier": "Early", "uncertain": True},
        ),
        (Script(), {"period": "None", "periodModifier": "None", "uncertain": None}),
    ],
)
def test_schema(script, serialized):
    assert ScriptSchema().load(serialized) == script
    assert ScriptSchema().dump(script) == serialized
