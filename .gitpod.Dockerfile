FROM gitpod/workspace-mongodb

# Install custom tools, runtime, etc. using apt-get
# More information: https://www.gitpod.io/docs/config-docker/
RUN sudo apt-get update \
    && sudo apt-get install -y \
        mongo-tools \
    && sudo rm -rf /var/lib/apt/lists/*

ARG PYTHON_VERSION=pypy3.7-7.3.5
RUN pyenv update
RUN pyenv install $PYTHON_VERSION
RUN pyenv global $PYTHON_VERSION

# See: https://github.com/gitpod-io/gitpod/issues/479
ENV PIP_USER=no
RUN python -m ensurepip
RUN pip install --upgrade pip poetry

ENV NODE_OPTIONS=--experimental-worker
ENV PYMONGOIM__MONGO_VERSION=4.4
ENV PYMONGOIM__OPERATING_SYSTEM=ubuntu
