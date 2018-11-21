import falcon


class FilesResource:
    # pylint: disable=R0903
    def __init__(self, files):
        self._files = files

    def on_get(self, req, resp, file_name):
        grid_out = self._files.find(file_name)

        self.check_scope(req, grid_out)

        resp.content_type = grid_out.content_type
        resp.stream_len = grid_out.length
        resp.stream = grid_out

    @staticmethod
    def check_scope(req, grid_out):
        file_scope = (grid_out.metadata or {}).get('scope')
        if (
                file_scope and
                not req.context['user'].has_scope(f'read:{file_scope}')
        ):
            raise falcon.HTTPForbidden()
