<!-- markdownlint-disable MD013 -->

# TODO: PR 1.1 — load defaults for every omittable token field

Plan: `TASK-chapter-plan-handoff.md`, "PR 1.1". Readers only, no write changes. Branch `sparse-token-load-defaults` from `origin/master` (`36c41664`).

- [x] Session start: memory and stale-data checks, cleanup
- [x] Check the plan against master and GitHub (0.1–0.3 merged; next is 1.1)
- [x] Create branch from `origin/master`; upstream unset (no accidental push to master)
- [x] Inventory token schemas: which fields have load defaults, which are required, which lack defaults
- [x] Re-check every omittable field against all infrastructure queries (handoff risk 1)
- [x] Add load defaults: `modifiers`, `flags`, `sign`; make `lemmatizable`/`alignable` not required
- [x] Confirm existing defaults: `enclosureType`, `namedEntities`, `realia`, `surrogate`, `variant`, `alignment`, `hasOmittedAlignment`, `hasVariantAlignment`, `erasure`, `nameBreaks`
- [x] Tests: per token schema, a sparse dict loads equal to the full dict
- [x] Tests: factory-built chapters and fragments, sparse stored shape loads equal (port of `lossless.py`)
- [x] Storage dump unchanged by this PR (no new omitted fields): 0.3's `test_token_storage_shapes.py` passes in the full suite
- [x] Run the service on a throwaway local DB seeded with sparse sample documents; exercise fragment and chapter routes
- [x] Gates: `task format`, `task lint`, pyre `--sequential`, pyright, `task test`, coverage 100% on changed files, flake8, mypy, qlty `--include-tests`, ≤250 lines
- [x] Self-check against every section of the Copilot instructions
- [x] Update `TASK-chapter-plan-handoff.md` status
- [x] Clean up: throwaway DBs, temp files, background processes; report memory
- [x] Wrap-up (requested 2026-11-04): docs and handoff current; markdownlint only (code unchanged since the gates)
- [x] Commit and push (on request); open the PR
- [ ] Remote checks green on the PR
- [ ] Your review and merge; deploy before PR 1.2
- [ ] Before merge: remove the `TASK-pr1.1-load-defaults-*` files from the branch

## Open findings

- `enclosureType` order in API output depends on the process's hash seed (`frozenset`). Harmless for the frontend; fix later by sorting on dump.
- `test_remove_alias_retires_reservation` is intermittent (1 failure in 3 full runs, passes alone). Cause unknown.
