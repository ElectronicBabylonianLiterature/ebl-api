def mock_json_file(contents, path) -> str:
    path = path / "test.json"
    with path.open("w") as tmp_file:
        tmp_file.write(contents)
    return str(path)
