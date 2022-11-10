import pytest
from ebl.fragmentarium.application.fragment_schema import ScriptSchema
from ebl.fragmentarium.domain.fragment import Script
from ebl.common.period import Period


@pytest.mark.parametrize(
    "script,serialized",
    [
        (Script(Period.FARA, True), {"period": "Fara", "uncertain": True}),
        (Script(), {"period": "None", "uncertain": False}),
    ],
)
def test_schema(script, serialized):
    assert ScriptSchema().load(serialized) == script
    assert ScriptSchema().dump(script) == serialized
