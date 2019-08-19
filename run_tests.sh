#!/usr/bin/env bash
set -e
pipenv flake8
pipenv mypy -p ebl
pipenv pytest --cov=ebl --cov-report term --cov-report xml
