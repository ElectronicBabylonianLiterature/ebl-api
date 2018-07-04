import falcon


class WordSearch:

    def __init__(self, dictionary):
        self.dictionary = dictionary

    @staticmethod
    def transform_object_id(word):
        result = dict(word)
        result['_id'] = str(word['_id'])
        return result

    def on_get(self, req, resp):
        if 'query' in req.params:
            words = self.dictionary.search(req.params['query'])
            resp.media = [self.transform_object_id(word) for word in words]
        else:
            resp.status = falcon.HTTP_UNPROCESSABLE_ENTITY
