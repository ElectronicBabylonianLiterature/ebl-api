from typing import Callable, Mapping, TypeVar, Tuple, Dict, Sequence


class DispatchError(Exception):
    pass


T = TypeVar("T")
Command = Callable[[Sequence[str]], T]
Dispatcher = Callable[[dict], T]


def get_parameter(parameters: Dict[str, str]) -> Tuple[str, Sequence[str]]:
    parameter = "+".join(parameters.keys())
    values = tuple(parameters.values())
    return parameter, values


def create_dispatcher(commands: Mapping[str, Command]) -> Dispatcher:
    def get_command(parameter: str) -> Command:
        try:
            return commands[parameter]
        except KeyError:
            raise DispatchError(f"Invalid parameter {parameter}.")

    def dispatch(parameters: Dict[str, str]) -> T:
        parameter, value = get_parameter(parameters)
        return get_command(parameter)(value)

    return dispatch
