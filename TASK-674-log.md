# TASK-674 Work Log

## 2026-03-16

- Received request to fix CI warnings and one failing test (`ebl/tests/dictionary/test_dictionary.py::test_changelog`).
- Confirmed branch baseline at commit `ce344861` with clean working tree before changes.
- Reproduced warning set locally in targeted tests; `test_changelog` did not fail locally but was stress-run 20 times to check flakiness.
- Implemented transient retry in `MongoCollection.insert_one` for `AutoReconnect` to reduce operation-cancelled flakes.
- Replaced deprecated `GridOut.contentType` property usage in `GridFsFile.content_type` with file document lookup.
- Added pytest warning filters for known third-party deprecations (`falcon`/`lark`/`falcon_caching`) in `pyproject.toml`.
- Targeted tests passed:
	- `ebl/tests/dictionary/test_dictionary.py::test_changelog`
	- `ebl/tests/files/test_images_route.py`
	- `ebl/tests/fragmentarium/test_folios_route.py`
	- `ebl/tests/fragmentarium/test_photos_route.py`
- Full suite passed: `3560 passed, 2 skipped, 1 xfailed`.
- Remaining warning is unrelated (`PytestUnraisableExceptionWarning` from temporary in-memory mongo cleanup in `test_app_bootstrap`).
