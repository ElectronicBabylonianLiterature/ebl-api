import pytest  # pyre-ignore

from ebl.dispatcher import DispatchError, create_dispatcher

COMMANDS = {"a": lambda value: f"a-{value}", "b": lambda value: f"b-{value}"}
DISPATCH = create_dispatcher(COMMANDS)


@pytest.mark.parametrize(
    "parameter,command",
    [(parameter, command) for parameter, command in COMMANDS.items()],
)
def test_valid_params(parameter, command):
    value = "value"
    assert DISPATCH({parameter: value}) == command(value)


@pytest.mark.parametrize(
    "parameters", [{}, {"invalid": "parameter"}, {"a": "a", "b": "b"}]
)
def test_invalid_params(parameters):
    with pytest.raises(DispatchError):
        DISPATCH(parameters)
