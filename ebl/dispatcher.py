from typing import Callable, Mapping, Tuple, TypeVar


class DispatchError(Exception):
    pass


T = TypeVar('T')
Command = Callable[[str], T]
Dispatcher = Callable[[dict], T]


def create_dispatcher(commands: Mapping[str, Command]) -> Dispatcher:
    def get_parameter(parameters: dict) -> Tuple[str, str]:
        if len(parameters) == 1:
            return next(iter(parameters.items()))
        else:
            raise DispatchError("Invalid number of parameters.")

    def get_command(parameter: str) -> Command:
        try:
            return commands[parameter]
        except KeyError:
            raise DispatchError(f'Invalid parameter {parameter}.')

    def execute_command(parameters: dict) -> T:
        parameter, value = get_parameter(parameters)
        return get_command(parameter)(value)

    return execute_command
