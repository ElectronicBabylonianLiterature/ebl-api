from typing import Callable, Mapping, TypeVar, Tuple, FrozenSet


class DispatchError(Exception):
    pass


T = TypeVar("T")
Command = Callable[[Mapping[str, str]], T]
Dispatcher = Callable[[Mapping[str, str]], T]


def get_parameter(
    parameters: Mapping[str, str]
) -> Tuple[FrozenSet[str], Mapping[str, str]]:
    parameter = frozenset(parameters.keys())
    values = parameters
    return parameter, values


def create_dispatcher(commands: Mapping[FrozenSet[str], Command[T]]) -> Dispatcher[T]:
    def get_command(parameter: FrozenSet[str]) -> Command[T]:
        try:
            return commands[parameter]
        except KeyError:
            raise DispatchError(f"Invalid parameter {parameter}.")

    def dispatch(parameters: Mapping[str, str]) -> T:
        parameter, value = get_parameter(parameters)
        return get_command(parameter)(value)

    return dispatch
