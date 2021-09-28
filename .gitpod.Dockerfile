FROM gitpod/workspace-mongodb

# Install custom tools, runtime, etc. using apt-get
# More information: https://www.gitpod.io/docs/config-docker/
RUN sudo apt-get update \
    && sudo apt-get install -y \
        mongo-tools \
    && sudo rm -rf /var/lib/apt/lists/*

RUN python -m ensurepip
RUN python -m pip install --upgrade pip pipenv

ENV NODE_OPTIONS=--experimental-worker
