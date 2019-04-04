import falcon
from ebl.errors import NotFoundError
from ebl.require_scope import require_scope
from ebl.corpus.text import Text


@falcon.before(require_scope, 'create:texts')
class TextsResource:
    # pylint: disable=R0903
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, 'create:texts')
    def on_put(self, req, resp):
        text = Text.from_dict(req.media)
        self._corpus.create(text, req.context['user'])
        resp.status = falcon.HTTP_NO_CONTENT


class TextResource:
    # pylint: disable=R0903
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, 'read:texts')
    def on_get(self, _, resp, category, index):
        try:
            text = self._corpus.find(int(category), int(index))
            resp.media = text.to_dict()
        except ValueError:
            raise NotFoundError(f'{category}.{index}')

    @falcon.before(require_scope, 'write:texts')
    def on_post(self, req, resp, category, index):
        text = Text.from_dict(req.media)
        try:
            self._corpus.update(
                int(category),
                int(index),
                text,
                req.context['user']
            )
            updated_text = self._corpus.find(text.category, text.index)
            resp.media = updated_text.to_dict()
        except ValueError:
            raise NotFoundError(f'{category}.{index}')
