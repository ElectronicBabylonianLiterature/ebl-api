from typing import Callable, FrozenSet, Mapping, Sequence, TypeVar
from inspect import signature


class DispatchError(Exception):
    pass


T = TypeVar("T")
Command = Callable[..., T]
Dispatcher = Callable[[Mapping[str, str]], T]


def get_parameter_names(parameters: Mapping[str, str]) -> FrozenSet[str]:
    return frozenset(parameters.keys())


def create_dispatcher(commands: Sequence[Command[T]]) -> Dispatcher[T]:
    command_map = {
        frozenset(signature(command).parameters.keys()): command for command in commands
    }
    if len(command_map) != len(commands):
        raise DispatchError("Duplicate arguments in commands.")

    def get_command(parameter_names: FrozenSet[str]) -> Command[T]:
        try:
            return command_map[parameter_names]
        except KeyError as error:
            raise DispatchError(f"Invalid parameters {parameter_names}.") from error

    def dispatch(parameters: Mapping[str, str]) -> T:
        parameter_names = get_parameter_names(parameters)
        return get_command(parameter_names)(**parameters)

    return dispatch
