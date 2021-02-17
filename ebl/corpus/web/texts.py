import falcon

from ebl.corpus.web.api_serializer import deserialize, serialize, serialize_public
from ebl.corpus.web.text_schemas import ApiTextSchema
from ebl.corpus.web.text_utils import create_text_id
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope


class TextsResource:
    auth = {"exempt_methods": ["GET"]}

    def __init__(self, corpus):
        self._corpus = corpus

    def on_get(self, _, resp: falcon.Response) -> None:
        texts = self._corpus.list()
        resp.media = [serialize_public(text) for text in texts]

    @falcon.before(require_scope, "create:texts")
    @validate(ApiTextSchema())
    def on_post(self, req: falcon.Request, resp: falcon.Response) -> None:
        text = deserialize(req.media)
        self._corpus.create(text, req.context.user)
        resp.status = falcon.HTTP_CREATED
        resp.location = f"/texts/{text.category}/{text.index}"
        resp.media = serialize(self._corpus.find(text.id))


class TextResource:
    def __init__(self, corpus):
        self._corpus = corpus

    @falcon.before(require_scope, "read:texts")
    def on_get(self, _, resp: falcon.Response, category: str, index: str) -> None:
        text = self._corpus.find(create_text_id(category, index))
        resp.media = serialize(text)
