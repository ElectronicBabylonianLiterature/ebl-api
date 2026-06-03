# TASK-717 Review — Devcontainer fix: auto-create `.env` and inject secrets

**PR:** [#717](https://github.com/ElectronicBabylonianLiterature/ebl-api/pull/717)
**Branch:** `fix-devcontainer` → `master`
**Date:** 2026-06-02
**Reviewer:** GitHub Copilot (AI)
**Cross-reference:** [ebl-frontend PR #733](https://github.com/ElectronicBabylonianLiterature/ebl-frontend/pull/733)
**Current status:** CHANGES\_REQUESTED (Fabdulla1, 2026-06-02)

---

## Summary

This PR fixes a devcontainer startup failure: Docker's `--env-file .env` in
`runArgs` causes container creation to fail when `.env` is absent (it is
gitignored). The fix adds `.devcontainer/init.sh` and wires it via
`initializeCommand` to create `.env` from `.env.example` and inject matching
Codespaces secrets before the container builds.

The core intent is correct and the approach would work in a Codespaces/Linux
environment. However, two design issues identified in existing reviews remain
unaddressed and block merge. The frontend PR #733 solves both of them with a
different lifecycle architecture that should be adopted here.

---

## Findings

### F-01 — `initializeCommand` requires `bash` and `python3` on the host

**Severity:** HIGH (BLOCKER — Fabdulla1 CHANGES\_REQUESTED, Copilot unresolved thread)

**Files:** `.devcontainer/devcontainer.json` line 15, `.devcontainer/init.sh`

#### Reproduction Steps

1. On a Windows host without WSL or Git Bash, open this repository in VS Code
   with Dev Containers.
2. VS Code runs `initializeCommand` on the host shell.
3. `bash` is not in PATH → container creation fails immediately, before the
   container is ever built.

#### Details

The current configuration:

```json
"initializeCommand": "bash .devcontainer/init.sh"
```

This string form is passed to the host shell. On Windows without WSL or
Git Bash, `bash` is unavailable. Even on systems that have `bash`, the
heredoc inside `init.sh` requires `python3` to also be present on the host
PATH.

The README documents "Linux, macOS, and GitHub Codespaces" as supported but
does not document Windows as unsupported. Windows contributors using Docker
Desktop + VS Code will hit this silently.

#### Recommendation

Split the work across two lifecycle phases, exactly as the frontend PR #733
does:

| Phase | Runs on | Responsibility |
| --- | --- | --- |
| `initializeCommand` | Host | Bootstrap `.env` from `.env.example` |
| `postCreateCommand` | Container | Inject Codespaces secrets (bash) |

**`devcontainer.json`:**

```json
"initializeCommand": ["sh", "-c", "test -f .env || cp .env.example .env"],
"postCreateCommand": "bash .devcontainer/setup.sh && bash .devcontainer/inject-secrets.sh"
```

Array form for `initializeCommand` bypasses the host shell entirely; the OS
invokes `sh` directly. `sh` is universally available on all POSIX hosts and
on Windows via Git Bash / WSL. The injection logic then moves to
`inject-secrets.sh` inside the container where `bash` and `python3` are
guaranteed by the `universal:2` base image.

---

### F-02 — Injection overwrites user-edited `.env` values on every rebuild

**Severity:** HIGH (BLOCKER — Fabdulla1 CHANGES\_REQUESTED)

**File:** `.devcontainer/init.sh`

#### Steps to reproduce (F-02)

1. Open a Codespace with matching secrets configured.
2. `init.sh` injects secrets into `.env`. Container starts.
3. User edits one `.env` value to a different value (e.g. a local
   MongoDB URI).
4. User rebuilds the container (routine operation).
5. `initializeCommand` runs again and overwrites the user's edit.

The user's change is silently lost.

#### Technical detail (F-02)

```python
for key in keys:
    if key in os.environ:
        value = os.environ[key].replace('\r', '').replace('\n', '')
        content = re.sub(...)   # always overwrites
```

#### Fix (F-02)

Compare the current `.env` value against the placeholder from
`.env.example`. Only inject if they still match (user-edited values
are preserved):

```python
with open('.env.example') as f:
    placeholders = {}
    for line in f:
        if line.strip() and not line.startswith('#') and '=' in line:
            k, v = line.strip().split('=', 1)
            placeholders[k.strip()] = v

for key in keys:
    if key in os.environ:
        current_match = re.search(
            r'^' + re.escape(key) + r'=(.*)',
            content,
            flags=re.MULTILINE
        )
        if current_match and current_match.group(1) != placeholders.get(key, ''):
            continue   # user has edited this value; do not clobber
        value = os.environ[key].replace('\r', '').replace('\n', '')
        content = re.sub(...)
```

The frontend `inject-secrets.sh` implements this guard at lines 36–38:
`if [ "$current_value" != "$template_value" ]; then continue; fi`.

---

### F-03 — No sync of new keys added to `.env.example` after initial setup

**Severity:** MEDIUM

**File:** `.devcontainer/init.sh`

#### Steps to reproduce (F-03)

1. User opens a Codespace — `.env` is created from `.env.example`.
2. A developer adds a new required key to `.env.example` and pushes.
3. User pulls and rebuilds the container.
4. `init.sh` skips the copy because `.env` already exists. The new
   key is never added to `.env`.
5. The application fails with a missing-variable error.

#### Fix (F-03)

Iterate over `.env.example` keys and append any key absent from the
current `.env`. The frontend `inject-secrets.sh` does this at
lines 28–33. A minimal Python equivalent:

```python
existing_keys = set(
    line.split('=')[0].strip()
    for line in content.splitlines()
    if line.strip() and not line.startswith('#') and '=' in line
)
appended = []
for key in keys:
    if key not in existing_keys:
        content += f'\n{key}={placeholders.get(key, "")}\n'
        appended.append(key)
if appended:
    print('Added missing keys to .env: ' + ', '.join(appended))
```

---

### F-04 — Unresolved Copilot thread: multi-line value newline handling

**Severity:** LOW (already handled in code; thread not marked resolved)

**File:** `.devcontainer/init.sh` line 33

The current code strips newlines from values before injection:

```python
value = os.environ[key].replace('\r', '').replace('\n', '')
```

This correctly prevents multi-line values from corrupting the `KEY=VALUE`
format that Docker's `--env-file` parser requires. The Copilot thread
(`PRRT_kwDOCBABsM6FEQK5`) remains unresolved on GitHub but the code already
addresses the concern. The thread should be marked resolved.

---

### F-05 — Unresolved Copilot thread: duplicate `.env` bootstrapping (already fixed)

**Severity:** LOW (code already correct; thread not marked resolved)

**File:** `.devcontainer/setup.sh`

The Copilot thread (`PRRT_kwDOCBABsM6FEQLe`) flagged the old `.env` creation
block in `setup.sh` as duplicate dead code. The PR diff shows that block was
already removed from `setup.sh`. The thread should be marked resolved.

---

## Cross-comparison: ebl-frontend PR #733

The frontend PR uses a more robust two-phase architecture that addresses all
backend blockers. Relevant patterns the backend should adopt:

- **`initializeCommand`**: Frontend uses array form `["sh", "-c", "..."]`
  — no host shell. Backend uses string `"bash ..."` — requires bash on host.
- **Injection timing**: Frontend uses `postCreateCommand` (inside
  container). Backend uses `initializeCommand` (on host, before build).
- **Clobber guard**: Frontend injects only if the value still matches the
  placeholder. Backend always overwrites, clobbering user edits on rebuild.
- **New-key sync**: Frontend appends keys missing from the env file.
  Backend does not.

**Recommendation:** Align the backend implementation to the frontend pattern.
The backend can retain its Python-based injection logic inside the container
(or convert to bash like the frontend), but the lifecycle split and
clobber-guard are both required before merge.

---

## Status of existing review threads

| Thread | Reviewer | Status in code | Thread state |
| ------ | -------- | -------------- | ------------ |
| `re.sub` backslash bug | sourcery-ai | ✅ Fixed (lambda) | Resolved |
| `if value:` vs `if key in os.environ:` | sourcery-ai | ✅ Fixed | Resolved |
| Capitalization in TASK-2-log.md | sourcery-ai | ✅ Fixed | Resolved |
| `lint:` task regression | copilot bot | ✅ Fixed (cmds restored) | Resolved |
| `lint-md` / npx not in container | copilot bot | ✅ Fixed | Resolved |
| `initializeCommand` host prereqs | copilot bot | ❌ Open | **Unresolved** |
| Multi-line value corruption | copilot bot | ✅ In code | **Unresolved** |
| setup.sh duplicate block | copilot bot | ✅ Removed in diff | **Unresolved** |
| Fabdulla1 (bash + clobber) | Fabdulla1 | ❌ Not fixed | **Blocking** |

---

## Overall Recommendation

**Do not merge** until F-01 and F-02 are resolved.

Suggested implementation order:

1. Convert `initializeCommand` to array form with shell-only copy.
2. Extract secret injection from `init.sh` into a new
   `inject-secrets.sh` that runs in `postCreateCommand`.
3. Add placeholder-guard to injection loop (don't clobber user edits).
4. Add missing-key sync (append new keys from `.env.example`).
5. Mark resolved threads as resolved on GitHub.
6. Remove `TASK-2-todo.md` and `TASK-2-log.md` before merge (task files
   must not be in the final PR).

---

## Round 2 Review — 2026-06-03

**Scope:** Audit of the current branch state after implementation of Round 1
findings, devcontainer failure debugging, and CodeQL security alert remediation.

**Branch HEAD:** `bbf4cfc7b` (after suppression commit reverted)

**Current state of changed files:**

- `.devcontainer/devcontainer.json` — updated
- `.devcontainer/init.sh` — deleted
- `.devcontainer/inject-secrets.py` — created (secret injection removed,
  new-key sync only)
- `.devcontainer/README.md` — updated
- `README.md` — updated

---

### New finding: F-06 — Script name no longer reflects its behaviour

**Severity:** MEDIUM

**File:** `.devcontainer/inject-secrets.py`

#### F-06 Details

After removing the secret-injection block (CodeQL remediation), the script
only appends missing placeholder keys from `.env.example` to `.env`. The
name `inject-secrets.py` now actively misleads contributors into thinking
the script writes secrets to disk, which it does not.

The `postCreateCommand` reference in `devcontainer.json` and descriptions
in both READMEs will also be inaccurate until the rename is applied.

#### F-06 Recommendation

Rename to `sync-env.py`. Update `postCreateCommand` in `devcontainer.json`
and all references in `.devcontainer/README.md` and `README.md`.

---

### New finding: F-07 — README ambiguous about `.env` and Codespaces runtime

**Severity:** MEDIUM

**File:** `.devcontainer/README.md`

#### F-07 Details

The current README states: "Codespaces secrets are injected as process
environment variables by the platform — they are never written to disk
by this project." While accurate, it does not explain the mechanism or
the continued role of `.env` at runtime.

Specifically:

- `.env` must still exist — `runArgs: ["--env-file", ".env"]` causes
  Docker to fail if the file is absent
- `.env` must contain all keys (placeholders if no real value is
  needed); `sync-env.py` ensures this
- In Codespaces, the platform passes `--secrets-file` to Docker, which
  translates to explicit `-e KEY=value` flags that **take precedence**
  over `--env-file` values — real secrets override placeholders at
  runtime without being written to the file
- Local (non-Codespaces) developers must still manually edit `.env`

The README implies `.env` plays a minor role, which could confuse
developers debugging missing-variable errors.

#### F-07 Recommendation

Add a "How it works" subsection explaining the two-layer env mechanism:

1. `.env` provides all keys (placeholders) for Docker via `--env-file`
2. Codespaces injects real values over the top at runtime via `-e`

---

### Cross-comparison Round 2: ebl-frontend PR #733

**New activity on frontend PR #733 (Fabdulla1, yesterday):**

Fabdulla1 raised three new review findings on the frontend PR that are
directly relevant here:

| Frontend finding | Backend? | Status |
| --- | --- | --- |
| `initializeCommand` hardcoded to `bash` | ✅ Same | ✅ Fixed |
| Injection via host env fails in Codespaces | ✅ Same | ✅ Fixed |
| New template key silently skipped | ✅ Same | ✅ Fixed |
| `.env.local` permissions too broad | N/A | Not applicable |
| `sudo` blocks non-interactive context | N/A | Not applicable |

The backend PR is ahead of the frontend PR on all shared concerns. However,
the frontend's `inject-secrets.sh` retains the Codespaces injection
approach — just moved inside the container. This differs from the backend's
decision to drop injection entirely and rely on Codespaces native env var
delivery. Both are valid; the backend approach is more secure (no
cleartext-to-disk path).

---

### Round 2 overall status

| Finding | Severity | Status |
| --- | --- | --- |
| F-01: host bash/python3 required | HIGH | ✅ Resolved |
| F-02: clobber guard missing | HIGH | ✅ Resolved (injection removed) |
| F-03: no new-key sync | MEDIUM | ✅ Resolved |
| F-04: multi-line value thread | LOW | ✅ Resolved on GitHub |
| F-05: setup.sh duplicate block thread | LOW | ✅ Resolved on GitHub |
| F-06: script name misleading | MEDIUM | ⬜ Pending |
| F-07: README ambiguous about `.env` runtime role | MEDIUM | ⬜ Pending |
| CodeQL clear-text storage | HIGH | ✅ Resolved at source |

**Do not merge** until F-06 and F-07 are addressed and task docs removed.
