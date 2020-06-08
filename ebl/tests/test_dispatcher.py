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
    "parameters", [{}, {"invalid": "parameter"}, {"a": "a", "b": "b", "c": "c"}]
)
def test_invalid_params(parameters):
    with pytest.raises(DispatchError):
        DISPATCH(parameters)


@pytest.mark.parametrize(
    "parameters", [{}, {"invalid": "parameter"}, {"a": "a", "b": "b"}]
)
def test_key_error(parameters):
    def raise_key_error(value):
        raise KeyError(value)

    parameter = "fail"
    message = "key error"
    with pytest.raises(KeyError, match=message):
        create_dispatcher({parameter: raise_key_error})({parameter: message})
