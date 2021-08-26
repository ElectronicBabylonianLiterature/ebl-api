import pytest

from ebl.dispatcher import DispatchError, create_dispatcher

COMMANDS = [lambda a: f"a: {a}", lambda b: f"b: {b}", lambda a, b: f"a: {a}, b: {b}"]
DISPATCH = create_dispatcher(COMMANDS)


@pytest.mark.parametrize(
    "parameters, results",
    [
        ({"a": "value"}, "a: value"),
        ({"b": "value"}, "b: value"),
        ({"a": "value1", "b": "value2"}, "a: value1, b: value2"),
    ],
)
def test_valid_parameters(parameters, results):
    assert DISPATCH(parameters) == results


@pytest.mark.parametrize(
    "parameters",
    [{}, {"invalid": "parameter"}, {"a": "a", "b": "b", "invalid": "parameter"}],
)
def test_invalid_parameters(parameters):
    with pytest.raises(DispatchError):
        DISPATCH(parameters)


def test_duplicate_parameters():
    with pytest.raises(DispatchError):
        create_dispatcher([lambda duplicate: False, lambda duplicate: True])


def test_key_error_from_command():
    message = "An error occurred in the command."

    def raise_error():
        raise KeyError(message)

    with pytest.raises(KeyError, match=message):
        create_dispatcher([raise_error])({})
