import falcon
from falcon.media.validators.jsonschema import validate
from ebl.require_scope import require_scope
from ebl.bibliography.bibliography_entry import CSL_JSON_SCHEMA


class BibliographyResource:
    # pylint: disable=R0903
    def __init__(self, bibliography):
        self._bibliography = bibliography

    @falcon.before(require_scope, 'write:bibliography')
    @validate(CSL_JSON_SCHEMA)
    def on_put(self, req, _resp):
        self._bibliography.create(req.media, req.context['user'])


class BibliographyEntriesResource:

    def __init__(self, bibliography):
        self._bibliography = bibliography

    @falcon.before(require_scope, 'read:bibliography')
    def on_get(self, _req, resp, id_):
        resp.media = self._bibliography.find(id_)

    @falcon.before(require_scope, 'write:bibliography')
    @validate(CSL_JSON_SCHEMA)
    def on_post(self, req, _resp, id_):
        entry = {**req.media, 'id': id_}
        self._bibliography.update(entry, req.context['user'])
