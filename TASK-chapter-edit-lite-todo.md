# TASK chapter-edit-lite: TODO

Goal: make the corpus chapter edit page load in seconds for large chapters.
This repository holds the API half; the page itself is in ebl-frontend.

## Done

- [x] `GET {chapter}/outline`: light chapter outline
- [x] `GET {chapter}/lines?offset=&limit=&tokens=`: lines in edit shape
- [x] `POST {chapter}/lines?view=outline`: light save response
- [x] Shared ATF helpers in `ebl/corpus/domain/line_atf.py`
- [x] Tests: domain, schemas, pagination, repository, routes
- [x] `ruff format --check ebl scripts`
- [x] `ruff check ebl scripts`
- [x] `pyre check`
- [x] `pyright`, `flake8`, `mypy` on the changed modules
- [x] Full `pytest` with the CI test environment
- [x] 100 % coverage of every new or changed module
- [x] Timed against Enūma eliš I replayed from production

## Open

- [ ] `qlty smells --include-tests` (qlty is not installed in the sandbox)
- [ ] Save path on real data (the sandbox database has no sign list)
- [ ] Permission to commit and push

## Later tasks

- [ ] Sparse alignment and lemmatization saves keyed by line index
- [ ] Faster write path: update only the changed line
- [ ] Revision check on save (409 on conflict)

## Before merge

- [ ] Remove `TASK-chapter-edit-lite-todo.md`
- [ ] Remove `TASK-chapter-edit-lite-log.md`
