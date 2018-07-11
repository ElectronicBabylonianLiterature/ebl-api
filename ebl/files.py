import falcon
from gridfs import GridFS


class FilesResource:
    # pylint: disable=R0903
    def __init__(self, database):
        self._fs = GridFS(database)

    def on_get(self, _req, resp, file_name):
        grid_out = self._fs.find_one({"filename": file_name})

        if grid_out is None:
            resp.status = falcon.HTTP_NOT_FOUND
        else:
            resp.content_type = grid_out.content_type
            resp.stream_len = grid_out.length
            resp.stream = grid_out
