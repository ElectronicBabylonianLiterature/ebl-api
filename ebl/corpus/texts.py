import falcon
from ebl.errors import NotFoundError
from ebl.require_scope import require_scope


class TextsResource:
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
