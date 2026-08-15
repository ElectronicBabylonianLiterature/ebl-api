import json

from falcon import Request, Response
from falcon_caching import Cache

from ebl.cache.application.cache import DEFAULT_TIMEOUT
from ebl.common.query.query_schemas import QueryResultSchema
from ebl.fragmentarium.application.fragment_repository import FragmentRepository


def make_latest_additions_resource(repository: FragmentRepository, cache: Cache):
    class LatestAdditionsResource:
        def __init__(
            self,
            repository: FragmentRepository,
        ):
            self._repository = repository

        @cache.cached(timeout=DEFAULT_TIMEOUT)
        def on_get(self, req: Request, resp: Response):
            resp.text = json.dumps(
                QueryResultSchema().dump(self._repository.query_latest())
            )

    return LatestAdditionsResource(repository)


def make_all_fragment_signs_resource(repository: FragmentRepository, cache: Cache):
    class AllFragmentSignsResource:
        def __init__(
            self,
            repository: FragmentRepository,
        ):
            self._repository = repository

        @cache.cached(timeout=DEFAULT_TIMEOUT)
        def on_get(self, req: Request, resp: Response):
            resp.text = json.dumps(self._repository.fetch_fragment_signs())

    return AllFragmentSignsResource(repository)


def make_all_fragment_ocred_signs_resource(
    repository: FragmentRepository, cache: Cache
):
    class AllFragmentOcredSignsResource:
        def __init__(
            self,
            repository: FragmentRepository,
        ):
            self._repository = repository

        @cache.cached(timeout=DEFAULT_TIMEOUT)
        def on_get(self, req: Request, resp: Response):
            resp.text = json.dumps(self._repository.fetch_fragment_ocred_signs())

    return AllFragmentOcredSignsResource(repository)
