from gridfs import GridFS


class GridFsFiles:
    # pylint: disable=R0903
    def __init__(self, database):
        self._fs = GridFS(database)

    def find(self, file_name):
        grid_out = self._fs.find_one({"filename": file_name})

        if grid_out is None:
            raise KeyError
        else:
            return grid_out
