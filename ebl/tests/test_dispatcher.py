import pytest

from ebl.dispatcher import DispatchError, create_dispatcher

COMMANDS = {
    frozenset(["a"]): lambda value: f"a_{''.join(value.values())}",
    frozenset(["b"]): lambda value: f"b_{''.join(value.values())}",
    frozenset(["a", "b"]): lambda value: f"a_b_{''.join(value.values())}",
}
DISPATCH = create_dispatcher(COMMANDS)


@pytest.mark.parametrize(
    "parameter, results",
    [
        ({"a": "value"}, "a_value"),
        ({"b": "value"}, "b_value"),
        ({"a": "value1", "b": "value2"}, "a_b_value1value2"),
    ],
)
def test_valid_params(parameter, results):
    assert DISPATCH(parameter) == results


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
        create_dispatcher({frozenset([parameter]): raise_key_error})(
            {parameter: message}
        )
