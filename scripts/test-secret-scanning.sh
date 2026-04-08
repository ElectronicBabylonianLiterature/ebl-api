#!/bin/sh
set -eu

cd "$(dirname "$0")/.."

if ! command -v ggshield >/dev/null 2>&1; then
    printf >&2 "ggshield is required to run secret scanning tests.\n"
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
    printf >&2 "ggshield authentication is required to run secret scanning tests.\n"
    printf >&2 "Authenticate using one of these methods:\n"
    printf >&2 "  1. Run: ggshield auth login\n"
    printf >&2 "  2. Export: GITGUARDIAN_API_KEY=<your-key>\n"
    exit 1
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "$tmp_dir"' EXIT HUP INT TERM

generate_alnum() {
    length="$1"
    tr -dc 'A-Za-z0-9' </dev/urandom | head -c "$length"
}

assert_passes() {
    name="$1"
    payload="$2"
    path="$tmp_dir/$name.env"
    printf '%s\n' "$payload" > "$path"

    if run_ggshield secret scan path "$path" >/dev/null 2>&1; then
        printf 'PASS %s\n' "$name"
    else
        printf >&2 'FAIL %s unexpectedly triggered detection\n' "$name"
        exit 1
    fi
}

assert_fails() {
    name="$1"
    payload="$2"
    path="$tmp_dir/$name.env"
    printf '%s\n' "$payload" > "$path"

    if run_ggshield secret scan path "$path" >/dev/null 2>&1; then
        printf >&2 'FAIL %s unexpectedly passed\n' "$name"
        exit 1
    else
        printf 'PASS %s\n' "$name"
    fi
}

ENV_EXAMPLE_PAYLOAD=$(cat <<'EOF'
# Auth0 Configuration
AUTH0_AUDIENCE=your-api-identifier
AUTH0_ISSUER=https://your-domain.auth0.com/
AUTH0_PEM=your-base64-encoded-certificate

# AI API Configuration
EBL_AI_API=http://localhost:8001

# MongoDB Configuration
MONGODB_DB=ebldev
MONGODB_URI=mongodb://localhost:27017/ebldev

# Sentry Configuration
SENTRY_DSN=https://your-sentry-dsn@sentry.io/project-id
SENTRY_ENVIRONMENT=development

GITGUARDIAN_API_KEY=gitguardian-api-key
EOF
)

MOCK_PEM="$(head -c 48 /dev/urandom | base64 | tr -d '\n')"
MOCK_GITGUARDIAN_PAT="gg_pat_$(generate_alnum 47)"
MOCK_GENERIC_KEY="$(generate_alnum 38)"

assert_passes "env-example-placeholders" "$ENV_EXAMPLE_PAYLOAD"
assert_fails "auth0-pem-mock-data" "AUTH0_PEM=$MOCK_PEM"
assert_fails "gitguardian-api-key" "GITGUARDIAN_API_KEY=${MOCK_GITGUARDIAN_PAT}"
assert_fails "generic-api-key" "api_key=\"${MOCK_GENERIC_KEY}\""

printf 'Secret scanning regression checks passed.\n'
