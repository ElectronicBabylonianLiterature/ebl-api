from typing import Any, Mapping, Optional

import attr
from gridfs import GridFS, GridOut
from pymongo.database import Database

from ebl.errors import NotFoundError
from ebl.files.application.file_repository import File, FileRepository


@attr.s(auto_attribs=True, frozen=True)
class GridFsFile(File):
    _grid_out: GridOut

    @property
    def metadata(self) -> Mapping[str, Any]:
        return self._grid_out.metadata or {}

    @property
    def length(self) -> int:
        return self._grid_out.length

    @property
    def content_type(self) -> Optional[str]:
        return self._grid_out.content_type

    def read(self, size=-1) -> bytes:
        return self._grid_out.read(size)

    def close(self) -> None:
        self._grid_out.close()


class GridFsFileRepository(FileRepository):
    def __init__(self, database: Database, collection: str):
        self._fs = GridFS(database, collection)

    def query_by_file_name(self, file_name: str) -> File:
        grid_out = self._fs.find_one({"filename": file_name})

        if grid_out is None:
            raise NotFoundError(f"File {file_name} not found.")
        else:
            return GridFsFile(grid_out)
