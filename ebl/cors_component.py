ONE_DAY = '86400'


class CorsComponent:
    """ Based on:
    https://falcon.readthedocs.io/en/stable/user/faq.html#how-do-i-implement-cors-with-falcon
    """

    def process_response(self, req, resp, _resource, req_succeeded):
        resp.set_header('Access-Control-Allow-Origin', '*')

        if (req_succeeded and self._is_preflight_request(req)):
            self._patch_preflight_response(req, resp)

    @staticmethod
    def _is_preflight_request(req):
        is_options = req.method == 'OPTIONS'
        request_method = req.get_header('Access-Control-Request-Method')
        return is_options and request_method

    @staticmethod
    def _patch_preflight_response(req, resp):
        allow = resp.get_header('Allow')
        resp.delete_header('Allow')

        allow_headers = req.get_header(
            'Access-Control-Request-Headers',
            default='*'
        )

        resp.set_headers((
            ('Access-Control-Allow-Methods', allow),
            ('Access-Control-Allow-Headers', allow_headers),
            ('Access-Control-Max-Age', ONE_DAY)
        ))
