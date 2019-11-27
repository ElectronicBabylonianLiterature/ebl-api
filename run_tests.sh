#!/usr/bin/env bash
set -e
pipenv run black ebl --check --diff
pipenv run flake8
pipenv run mypy -p ebl
pipenv run pytest --cov=ebl --cov-report term --cov-report xml
