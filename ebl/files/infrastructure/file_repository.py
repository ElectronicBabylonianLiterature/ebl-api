from gridfs import GridFS

from ebl.errors import NotFoundError


class GridFsFiles:

    def __init__(self, database):
        self._fs = GridFS(database)

    def find(self, file_name):
        grid_out = self._fs.find_one({"filename": file_name})

        if grid_out is None:
            raise NotFoundError(f'File {file_name} not found.')
        else:
            return grid_out
