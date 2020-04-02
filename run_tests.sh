#!/usr/bin/env bash
set -e
flake8 ebl
pyre check --typeshed "${VIRTUAL_ENV}/lib/pyre_check/typeshed"
pytest
