from typing import Callable, Mapping, TypeVar, FrozenSet


class DispatchError(Exception):
    pass


T = TypeVar("T")
V = TypeVar("V")
Command = Callable[[Mapping[str, V]], T]
Dispatcher = Callable[[Mapping[str, V]], T]


def get_parameter_names(parameters: Mapping[str, V]) -> FrozenSet[str]:
    return frozenset(parameters.keys())


def create_dispatcher(
    commands: Mapping[FrozenSet[str], Command[V, T]],
) -> Dispatcher[V, T]:
    def get_command(parameter_names: FrozenSet[str]) -> Command[V, T]:
        try:
            return commands[parameter_names]
        except KeyError as error:
            raise DispatchError(f"Invalid parameters {parameter_names}.") from error

    def dispatch(parameters: Mapping[str, V]) -> T:
        parameter_names = get_parameter_names(parameters)
        return get_command(parameter_names)(parameters)

    return dispatch
