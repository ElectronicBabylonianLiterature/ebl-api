from ebl.files.infrastructure.grid_fs_file_repository import GridFsFileRepository


def test_content_type_falls_back_to_metadata_content_type(database) -> None:
    repository = GridFsFileRepository(database, "metadata_only_files")

    repository._fs.put(
        b"content",
        filename="metadata-content-type.jpg",
        metadata={"contentType": "image/png"},
    )

    file = repository.query_by_file_name("metadata-content-type.jpg")

    assert file.content_type == "image/png"
