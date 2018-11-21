class DispatchError(Exception):
    pass


def create_dispatcher(commands):
    def get_parameter(parameters):
        if len(parameters) == 1:
            return next(iter(parameters.items()))
        else:
            raise DispatchError("Invalid number of parameters.")

    def get_command(parameter):
        if parameter in commands:
            return commands[parameter]
        else:
            raise DispatchError(f'Invalid parameter {parameter}.')

    def execute_command(request):
        parameter, value = get_parameter(request)
        return get_command(parameter)(value)

    return execute_command
