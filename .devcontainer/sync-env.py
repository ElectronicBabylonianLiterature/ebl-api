#!/usr/bin/env python3


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
    appended: list[str] = []

    for key, placeholder in placeholders.items():
        if key not in current:
            modified = modified.rstrip('\n') + f'\n{key}={placeholder}\n'
            appended.append(key)

    if appended:
        with open('.env', 'w') as f:
            f.write(modified)
        print('Added missing keys to .env: ' + ', '.join(appended))
    else:
        print('.env already contains all keys from .env.example')


if __name__ == '__main__':
    main()
