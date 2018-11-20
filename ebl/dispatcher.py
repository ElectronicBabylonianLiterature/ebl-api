import falcon


def create_dispatcher(commands):
    def get_parameter(request):
        parameter_names = list(request.params)
        if len(parameter_names) == 1:
            parameter = parameter_names[0]
            return parameter, request.params[parameter]
        else:
            raise falcon.HTTPUnprocessableEntity()

    def get_command(param):
        if param in commands:
            return commands[param]
        else:
            raise falcon.HTTPUnprocessableEntity()

    def execute_command(request):
        param, value = get_parameter(request)
        return get_command(param)(value)

    return execute_command
