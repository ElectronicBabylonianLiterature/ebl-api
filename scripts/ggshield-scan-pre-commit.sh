#!/bin/sh
set -eu

if ! command -v ggshield >/dev/null 2>&1; then
    printf >&2 "\nggshield is required for secret scanning. Install it or rebuild the devcontainer.\n\n"
    exit 1
fi

run_ggshield() {
    if [ "${GITGUARDIAN_API_KEY+x}" = x ] && [ -z "${GITGUARDIAN_API_KEY}" ]; then
        env -u GITGUARDIAN_API_KEY ggshield "$@"
    else
        ggshield "$@"
    fi
}

if ! run_ggshield api-status >/dev/null 2>&1; then
    printf >&2 "\nggshield authentication is required for secret scanning.\n"
    printf >&2 "Authenticate using one of these methods:\n"
    printf >&2 "  1. Run: ggshield auth login\n"
    printf >&2 "  2. Export: GITGUARDIAN_API_KEY=<your-key>\n\n"
    exit 1
fi

run_ggshield secret scan pre-commit
