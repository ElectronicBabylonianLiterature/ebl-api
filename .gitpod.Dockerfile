FROM gitpod/workspace-mongodb

# Install custom tools, runtime, etc. using apt-get
# For example, the command below would install "bastet" - a command line tetris clone:
#
# RUN sudo apt-get update \
#     && sudo apt-get install -y \
#         ... \
#     && rm -rf /var/lib/apt/lists/*
# More information: https://www.gitpod.io/docs/42_config_docker/
RUN brew install python@3.8
