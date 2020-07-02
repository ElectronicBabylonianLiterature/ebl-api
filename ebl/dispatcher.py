from typing import Callable, Mapping, TypeVar, Union, Tuple, Any

from ebl.errors import DataError


class DispatchError(Exception):
    pass


T = TypeVar("T")
Command = Callable[[str], T]
Dispatcher = Callable[[dict], T]


def _check_pages(pages: Union[str, None]) -> str:
    if pages:
        try:
            int(pages)
            return pages
        except ValueError:
            raise DataError(f'Pages "{pages}" not numeric.')
    else:
        return ""


def get_parameter(parameters: dict) -> Tuple[str, Any]:
    if len(parameters) == 1:
        return next(iter(parameters.items()))
    elif len(parameters) == 2:
        parameters["pages"] = _check_pages(parameters.get("pages"))
        return "reference", parameters
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
