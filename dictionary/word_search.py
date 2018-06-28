class WordSearch:

    def __init__(self, dictionary):
        self.dictionary = dictionary

    @staticmethod
    def transform_object_id(word):
        result = dict(word)
        result['_id'] = str(word['_id'])
        return result

    def on_get(self, req, resp, query):
        words = self.dictionary.search(query)
        resp.media = [self.transform_object_id(word) for word in words]
