from typing import Callable, Mapping, TypeVar, FrozenSet


class DispatchError(Exception):
    pass


T = TypeVar("T")
Command = Callable[[Mapping[str, str]], T]
Dispatcher = Callable[[Mapping[str, str]], T]


def get_parameter_names(parameters: Mapping[str, str]) -> FrozenSet[str]:
    return frozenset(parameters.keys())


def create_dispatcher(commands: Mapping[FrozenSet[str], Command[T]]) -> Dispatcher[T]:
    def get_command(parameter_names: FrozenSet[str]) -> Command[T]:
        try:
            return commands[parameter_names]
        except KeyError as error:
            raise DispatchError(f"Invalid parameters {parameter_names}.") from error

    def dispatch(parameters: Mapping[str, str]) -> T:
        parameter_names = get_parameter_names(parameters)
        return get_command(parameter_names)(parameters)

    return dispatch
