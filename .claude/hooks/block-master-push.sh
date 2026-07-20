#!/usr/bin/env bash
#
# Claude Code PreToolUse guard for Bash calls.
# Exit 2 => block the tool call. Exit 0 => allow.
#
# Blocks:
#   1. any `git push` that targets master (direct push to the protected branch)
#   2. any force-push (--force / --force-with-lease / -f)
#
set -euo pipefail

payload=$(cat)
command=$(printf '%s' "$payload" | jq -r '.tool_input.command // ""')

# Only inspect git push invocations.
if ! printf '%s' "$command" | grep -qE '(^|[^[:alnum:]_])git[[:space:]]+push'; then
    exit 0
fi

if printf '%s' "$command" | grep -qE -- '(--force([^-]|$)|--force-with-lease|(^|[[:space:]])-f([[:space:]]|$))'; then
    echo "BLOCKED: force-push is forbidden in this repository." >&2
    echo "If a history rewrite is truly required, the human operator must run it." >&2
    exit 2
fi

if printf '%s' "$command" | grep -qE '(^|[[:space:]:])(refs/heads/)?master([[:space:]]|$)'; then
    echo "BLOCKED: pushing to master is forbidden." >&2
    echo "master changes only through a reviewed, merged pull request." >&2
    exit 2
fi

exit 0
