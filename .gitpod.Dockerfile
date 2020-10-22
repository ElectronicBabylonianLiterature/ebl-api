FROM gitpod/workspace-mongodb

# Install custom tools, runtime, etc. using apt-get
# For example, the command below would install "bastet" - a command line tetris clone:
#
# RUN sudo apt-get update \
#     && sudo apt-get install -y \
#         ... \
#     && rm -rf /var/lib/apt/lists/*
# More information: https://www.gitpod.io/docs/42_config_docker/
ARG PYTHON_VERSION=pypy3.6-7.3.1
RUN pyenv install $PYTHON_VERSION
RUN pyenv global $PYTHON_VERSION
RUN python -m ensurepip
RUN python -m pip install --upgrade pip pipenv

ENV NODE_OPTIONS=--experimental-worker
