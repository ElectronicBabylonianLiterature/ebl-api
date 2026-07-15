# TASK-realia-review-fixes — TODO

Address the findings from `TASK-realia-annotation-review.md`.

- [x] F1 — cover the markup parse-error branch in
  `domain/fragment_metadata.py:19-20` (coverage hard gate).
- [x] F2 — replace the per-id realia existence check in
  `web/named_entities.py` with the batch `find_by_realia_ids`.
- [x] F3 — short-circuit `application/realia_info.py::resolve_realia_info` on
  empty realia; update `test_resolve_empty_without_realia`.
- [x] F4 — WITHDRAWN: write-side `realiaInfo` omission is intentional and
  test-guarded; exploratory change reverted.
- [x] F5 — resolved as intentional (round-trip schema is deliberately tested);
  no code change.
- [ ] F6 — remove all `TASK-*.md` before merge (reminder only).
- [x] Gates — format, tests, 100% coverage on changed files, lint, types.
