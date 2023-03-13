from ebl.dispatcher import create_dispatcher


class WordSearch:
    def __init__(self, dictionary):
        self._dispatch = create_dispatcher(
            {
                frozenset(["query"]): lambda value: dictionary.search(**value),
                frozenset(["lemma"]): lambda value: dictionary.search_lemma(**value),
                frozenset(["lemmas"]): lambda value: dictionary.find_many(
                    value["lemmas"].split(",")
                ),
                frozenset(["listAll"]): lambda value: dictionary.list_all_words(),
            }
        )

    def on_get(self, req, resp):
        resp.media = self._dispatch(req.params)
