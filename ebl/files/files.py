import falcon


class FilesResource:
    # pylint: disable=R0903
    def __init__(self, files):
        self._files = files

    def on_get(self, _req, resp, file_name):
        try:
            grid_out = self._files.find(file_name)

            resp.content_type = grid_out.content_type
            resp.stream_len = grid_out.length
            resp.stream = grid_out
        except KeyError:
            resp.status = falcon.HTTP_NOT_FOUND
