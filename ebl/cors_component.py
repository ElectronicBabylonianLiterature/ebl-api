
class CORSComponent(object):
    """
    From https://falcon.readthedocs.io/en/stable/user/faq.html#how-do-i-implement-cors-with-falcon
    """  # noqa
    # pylint: disable=R0903

    def process_response(self, req, resp, _resource, req_succeeded):
        # pylint: disable=R0201
        resp.set_header('Access-Control-Allow-Origin', '*')

        is_options = req.method == 'OPTIONS'
        request_method = req.get_header('Access-Control-Request-Method')
        if (req_succeeded and is_options and request_method):
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
