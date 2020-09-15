from typing import Callable, Mapping, TypeVar, Tuple, Dict, FrozenSet


class DispatchError(Exception):
    pass


T = TypeVar("T")
Command = Callable[[Mapping[str, str]], T]
Dispatcher = Callable[[dict], T]


def get_parameter(
    parameters: Dict[str, str]
) -> Tuple[FrozenSet[str], Mapping[str, str]]:
    parameter = frozenset(parameters.keys())
    values = parameters
    return parameter, values


def create_dispatcher(commands: Mapping[FrozenSet[str], Command]) -> Dispatcher:
    def get_command(parameter: FrozenSet[str]) -> Command:
        try:
            return commands[parameter]
        except KeyError:
            raise DispatchError(f"Invalid parameter {parameter}.")

    def dispatch(parameters: Dict[str, str]) -> T:
        parameter, value = get_parameter(parameters)
        return get_command(parameter)(value)

    return dispatch
