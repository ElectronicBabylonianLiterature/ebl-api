import json
import falcon

from .dictionary import Dictionary
from .words import WordsResource

class CORSComponent(object):
    # From https://falcon.readthedocs.io/en/stable/user/faq.html#how-do-i-implement-cors-with-falcon

    # pylint: disable=R0201
    def process_response(self, req, resp, resource, req_succeeded):
        resp.set_header('Access-Control-Allow-Origin', '*')

        if (req_succeeded
                and req.method == 'OPTIONS'
                and req.get_header('Access-Control-Request-Method')
           ):
            # NOTE(kgriffs): This is a CORS preflight request. Patch the
            #   response accordingly.

            allow = resp.get_header('Allow')
            resp.delete_header('Allow')

            allow_headers = req.get_header(
                'Access-Control-Request-Headers',
                default='*'
            )

            resp.set_headers((
                ('Access-Control-Allow-Methods', allow),
                ('Access-Control-Allow-Headers', allow_headers),
                ('Access-Control-Max-Age', '86400'),  # 24 hours
            ))

def create_app(dictionary_path):
    with open(dictionary_path, encoding='utf8') as dictionary_json:
        dictionary = Dictionary(json.load(dictionary_json))

    api = falcon.API(middleware=CORSComponent())

    words = WordsResource(dictionary)
    api.add_route('/words/{lemma}/{homonym}', words)

    return api
