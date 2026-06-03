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
