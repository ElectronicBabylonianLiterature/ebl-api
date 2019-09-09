from typing import Callable, Mapping, Tuple, TypeVar


class DispatchError(Exception):
    pass


T = TypeVar('T')
Command = Callable[[str], T]
Dispatcher = Callable[[dict], T]


def get_parameter(parameters: dict) -> Tuple[str, str]:
    if len(parameters) == 1:
        return next(iter(parameters.items()))
    else:
        raise DispatchError("Invalid number of parameters.")


def create_dispatcher(commands: Mapping[str, Command]) -> Dispatcher:
    def dispatch(parameters: dict) -> T:
        parameter, value = get_parameter(parameters)
        try:
            return commands[parameter](value)
        except KeyError:
            raise DispatchError(f'Invalid parameter {parameter}.')

    return dispatch
