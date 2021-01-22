FROM gitpod/workspace-mongodb

# Install custom tools, runtime, etc. using apt-get
# More information: https://www.gitpod.io/docs/config-docker/
RUN sudo apt-get update \
    && sudo apt-get install -y \
        mongo-tools \
    && sudo rm -rf /var/lib/apt/lists/*

ARG PYTHON_VERSION=pypy3.7-7.3.3
RUN pyenv install $PYTHON_VERSION
RUN pyenv global $PYTHON_VERSION
RUN python -m ensurepip
RUN python -m pip install --upgrade pip pipenv

ENV NODE_OPTIONS=--experimental-worker
