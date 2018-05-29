import falcon

class WordsResource:
    dictionary = [
        {
            'lemma': ['part1', 'part2'],
            'homonym': 'homonym'
        }
    ]

    def on_get(self, req, resp, lemma, homonym):
        compoundLemma = lemma.split(' ')
        words = [word for word in WordsResource.dictionary if word['lemma'] == compoundLemma]

        if(len(words) > 0):
            resp.media = words[0]
        else:
            resp.status = falcon.HTTP_NOT_FOUND

api = application = falcon.API()
api.add_route('/words/{lemma}/{homonym}', WordsResource())
