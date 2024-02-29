FROM gitpod/workspace-mongodb

# Install custom tools, runtime, etc. using apt-get
# More information: https://www.gitpod.io/docs/config-docker/
RUN sudo apt-get update \
    && sudo apt-get install -y \
        mongo-tools \
    && sudo rm -rf /var/lib/apt/lists/*

RUN brew install go-task/tap/go-task

ARG PYTHON_VERSION=pypy3.9-7.3.10
RUN cd /home/gitpod/.pyenv/plugins/python-build/../.. && git pull && cd -
RUN pyenv install $PYTHON_VERSION
RUN pyenv global $PYTHON_VERSION

RUN python -m ensurepip
RUN python -m pip install --upgrade pip poetry numpy pandas

ENV NODE_OPTIONS=--experimental-worker
ENV PYMONGOIM__MONGO_VERSION=4.4
ENV PYMONGOIM__OPERATING_SYSTEM=ubuntu
