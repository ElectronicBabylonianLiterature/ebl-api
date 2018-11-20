import falcon
import pytest
from ebl.dispatcher import create_dispatcher


class RequestStub:
    # pylint: disable=R0903
    def __init__(self, params):
        self.params = params


COMMANDS = {
    'a': lambda value: f'a-{value}',
    'b': lambda value: f'b-{value}'
}


DISPATCH = create_dispatcher(COMMANDS)


@pytest.mark.parametrize("param,command", [
    (param, command) for param, command in COMMANDS.items()
])
def test_valid_params(param, command):
    value = 'value'
    assert DISPATCH(RequestStub({param: value})) == command(value)


@pytest.mark.parametrize("params", [
    {},
    {'invalid': 'parameter'},
    {'a': 'a', 'b': 'b'}
])
def test_invalid_params(params):
    with pytest.raises(falcon.HTTPUnprocessableEntity):
        DISPATCH(RequestStub(params))
