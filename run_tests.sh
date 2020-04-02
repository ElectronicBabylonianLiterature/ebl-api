#!/usr/bin/env bash
set -e
flake8 ebl
pyre --typeshed "${VIRTUAL_ENV}/lib/pyre_check/typeshed" check
pytest
