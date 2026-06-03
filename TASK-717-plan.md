# TASK-717 Plan — Address Review Findings

**Date:** 2026-06-02
**Based on:** TASK-717-review.md
**Scope:** 5 files changed, 1 file deleted, 1 file created

---

## Findings addressed

| ID | Severity | Root cause |
| -- | -------- | ---------- |
| F-01 | HIGH (blocker) | bash required on host by `initializeCommand` |
| F-02 | HIGH (blocker) | injection clobbers user edits |
| F-03 | MEDIUM | missing keys not appended to `.env` |
| F-04 | LOW | thread needs marking (already in code) |
| F-05 | LOW | thread needs marking (already in code) |

---

## Architecture change

The fix mirrors the approach in ebl-frontend PR #733:

| Phase | Where | Responsibility |
| --- | --- | --- |
| `initializeCommand` | Host, before build | POSIX `sh` copy; bash not needed |
| `postCreateCommand` | Container, after build | Inject secrets + sync keys |

---

## File-by-file changes

### 1. `.devcontainer/devcontainer.json`

**Change `initializeCommand`** from string to array and extend
`postCreateCommand` to call the new inject script.

**Before:**

```json
"initializeCommand": "bash .devcontainer/init.sh",
...
"postCreateCommand": "bash .devcontainer/setup.sh",
```

**After:**

```json
"initializeCommand": ["sh", "-c", "test -f .env || cp .env.example .env"],
...
"postCreateCommand": "bash .devcontainer/setup.sh && python3 .devcontainer/inject-secrets.py",
```

The array form for `initializeCommand` bypasses the host shell entirely;
the OS invokes `sh` directly. `sh` is available on all POSIX hosts and on
Windows via Git Bash / WSL. No `bash` or `python3` required on the host.

---

### 2. `.devcontainer/init.sh` → **DELETE**

All responsibilities are now distributed:

- File copy → inline in `initializeCommand` above.
- Secret injection → new `inject-secrets.py` running in the container.

---

### 3. New `.devcontainer/inject-secrets.py`

New Python script that runs inside the container as part of
`postCreateCommand`.

**Responsibilities:**

1. Read all keys and placeholder values from `.env.example`.
2. For each key **absent** from `.env`: append `key=placeholder` (new-key
   sync — fixes F-03).
3. For each key **present in both** `.env` and the host environment: inject
   the secret value only if the current `.env` value still matches the
   placeholder (clobber guard — fixes F-02).
4. Write back to `.env` only if any change was made.
5. Print a clear summary of injected keys, appended keys, or "no secrets
   found".

**Full content:**

```python
#!/usr/bin/env python3
import os
import re


def read_file(path: str) -> str:
    with open(path) as f:
        return f.read()


def parse_env(content: str) -> dict[str, str]:
    result: dict[str, str] = {}
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if '=' in stripped:
            key, _, value = stripped.partition('=')
            result[key.strip()] = value
    return result


def main() -> None:
    example_content = read_file('.env.example')
    placeholders = parse_env(example_content)

    env_content = read_file('.env')
    current = parse_env(env_content)

    modified = env_content
    injected: list[str] = []
    appended: list[str] = []

    for key, placeholder in placeholders.items():
        if key not in current:
            modified = modified.rstrip('\n') + f'\n{key}={placeholder}\n'
            appended.append(key)
        elif key in os.environ:
            secret_value = os.environ[key].replace('\r', '').replace('\n', '')
            if current[key] == placeholder:
                modified = re.sub(
                    r'^' + re.escape(key) + r'=.*',
                    lambda m, k=key, v=secret_value: f'{k}={v}',
                    modified,
                    flags=re.MULTILINE,
                )
                injected.append(key)

    if injected or appended:
        with open('.env', 'w') as f:
            f.write(modified)

    if appended:
        print('Added missing keys to .env: ' + ', '.join(appended))
    if injected:
        print('Injected Codespaces secrets into .env: ' + ', '.join(injected))
    if not injected and not appended:
        print(
            'No Codespaces secrets found'
            ' \u2014 .env uses placeholder values from .env.example'
        )


if __name__ == '__main__':
    main()
```

**Design notes:**

- `parse_env` strips leading whitespace before `#` so indented comments
  are correctly ignored (fixes the Sourcery finding that the original
  key-parsing in `init.sh` lacked this).
- `current[key] == placeholder` guard ensures user-edited values are
  never clobbered (fixes F-02).
- Missing-key append uses `.rstrip('\n') + '\n{key}={placeholder}\n'` to
  guarantee a clean newline boundary regardless of whether the file has a
  trailing newline (same principle as the frontend's `printf '\n%s\n'`
  fix).
- `lambda m, k=key, v=secret_value:` uses default-argument capture so the
  correct `key`/`secret_value` values are used inside the loop (avoids
  late-binding closure bug).

---

### 4. `.devcontainer/README.md`

**Replace the "Automatic Setup" step** to describe the two-phase lifecycle
and remove the Windows host-prerequisite caveat (no longer needed).

**Before:**

```md
1. **Automatic Setup**: Before the container is created, `initializeCommand` runs
   `.devcontainer/init.sh` on the host. This script:
   - Creates `.env` from `.env.example` if `.env` does not already exist.
   - For each key defined in `.env.example`, if a Codespaces secret ...
     written into `.env`, replacing the placeholder. ...

   > **Host prerequisites**: `initializeCommand` runs on the host machine
   > before the container is built. It requires `bash` and `python3` on the
   > host `PATH`. ...
```

**After:**

```md
1. **Automatic Setup**: Environment configuration happens in two phases:
   - **Before container build** (`initializeCommand`): Creates `.env` from
     `.env.example` if it does not already exist. This step uses only POSIX
     `sh` and works on all host platforms (Linux, macOS, Windows with Git
     Bash or WSL, Codespaces). No bash or Python required on the host.
   - **After container build** (`postCreateCommand`): Runs
     `inject-secrets.py` inside the container. This script:
     - Injects any [Codespaces secrets][cs] whose names match keys in
       `.env.example`, but only if the current `.env` value still matches
       the placeholder (user-edited values are preserved on rebuild).
     - Appends any keys present in `.env.example` but missing from `.env`,
       keeping your environment in sync when new variables are introduced.
```

**Update the "Files" section** to replace `init.sh` with
`inject-secrets.py`.

---

### 5. `README.md`

**Update the "Getting Started" step 1** to replace references to
`init.sh` with the new two-phase description and correct the Codespaces
secret injection timing (it now happens after container build, not before).

**Before (relevant lines):**

```md
   Before the container is built, `.devcontainer/init.sh` runs
   automatically and creates `.env` from `.env.example` if it does not
   already exist. No manual copy step is needed.
...
   **Tip — skip this step with Codespaces secrets**: If you configure
   your credentials as [Codespaces secrets][codespaces-secrets] using the
   same names as the keys in `.env.example`, `init.sh` will inject them
   into `.env` automatically and the container will be fully configured
   on first start with no manual editing.
```

**After:**

```md
   Before the container is built, `.env` is created automatically from
   `.env.example` if it does not already exist. No manual copy step is
   needed.
...
   **Tip — skip this step with Codespaces secrets**: Configure your
   credentials as [Codespaces secrets][codespaces-secrets] using the same
   names as the keys in `.env.example`. After the container is built,
   `inject-secrets.py` runs automatically and injects them into `.env`.
   The container will be fully configured with no manual editing.
```

---

## Implementation order

1. Delete `.devcontainer/init.sh`
2. Create `.devcontainer/inject-secrets.py`
3. Edit `.devcontainer/devcontainer.json`
4. Edit `.devcontainer/README.md`
5. Edit `README.md`
6. Run `task lint-md` — must pass with zero errors
7. Test manually inside the devcontainer (verify injection, new-key sync,
   and clobber guard all work as expected)
8. Push — do **not** commit or push without explicit user approval

---

## Out of scope

- `Taskfile.dist.yml` — `lint:` task regression and `lint-md` thread are
  already resolved in the current diff; no further changes needed.
- `.devcontainer/setup.sh` — duplicate `.env` block already removed in
  this PR; no further changes needed.
- `TASK-2-todo.md` / `TASK-2-log.md` — already absent from the working
  tree; no action needed.
- GitHub thread resolution (F-04, F-05) — mark threads as resolved on
  GitHub after pushing the fix (separate UI action).
