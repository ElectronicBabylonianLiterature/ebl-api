from typing import Callable, Mapping, Tuple, TypeVar, Any

from ebl.errors import DataError


class DispatchError(Exception):
    pass


T = TypeVar("T")
Command = Callable[[str], T]
Dispatcher = Callable[[dict], T]


def _check_pages(pages: str) -> None:
    try:
        int(pages)
    except ValueError:
        raise DataError(f'Pages "{pages}" not numeric.')


def get_parameter(parameters: dict) -> Tuple[str, Any]:
    if len(parameters) == 1:
        return next(iter(parameters.items()))
    elif len(parameters) == 2:
        if "pages" in parameters:
            if parameters["pages"] == "":
                parameters["pages"] = None
            else:
                _check_pages(parameters["pages"])
        return ("reference", parameters)
    else:
        raise DispatchError("Invalid number of parameters.")


def create_dispatcher(commands: Mapping[str, Command]) -> Dispatcher:
    def get_command(parameter: str) -> Command:
        try:
            return commands[parameter]
        except KeyError:
            raise DispatchError(f"Invalid parameter {parameter}.")

    def dispatch(parameters: dict) -> T:
        parameter, value = get_parameter(parameters)
        return get_command(parameter)(value)

    return dispatch
