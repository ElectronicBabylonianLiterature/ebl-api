import falcon

from ebl.openapi.web.resource import OpenApiResource


def create_open_api_route(api: falcon.API,  spec):
    open_api = OpenApiResource(spec)
    api.add_route('/ebl.yml', open_api)
    spec.path(resource=open_api)
