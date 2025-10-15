#!/bin/bash
set -e

# Install MongoDB 4.4 if not already installed
if ! command -v mongod &> /dev/null; then
    echo "Installing MongoDB 4.4..."
    sudo apt-get update
    sudo apt-get install -y gnupg wget curl

    # Add MongoDB GPG key and repository
    wget -qO - https://www.mongodb.org/static/pgp/server-4.4.asc | sudo apt-key add -
    echo "deb [ arch=amd64,arm64 ] https://repo.mongodb.org/apt/ubuntu focal/mongodb-org/4.4 multiverse" | sudo tee /etc/apt/sources.list.d/mongodb-org-4.4.list

    # Install MongoDB and mongo-tools
    sudo apt-get update
    sudo apt-get install -y mongodb-org mongodb-org-tools mongo-tools
else
    echo "MongoDB already installed, skipping..."
fi

echo "Verifying go-task installation..."
# go-task is installed via devcontainer feature
if ! command -v task &> /dev/null; then
    echo "❌ go-task not found! This should be installed via devcontainer feature."
    exit 1
fi
task --version

echo "Installing Rust (required for libcst/pyre-check)..."
# Install Rust compiler (needed for libcst which is required by pyre-check)
if ! command -v rustc &> /dev/null; then
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
    source $HOME/.cargo/env
else
    echo "Rust already installed, skipping..."
fi

echo "Verifying poetry installation..."
# Poetry is installed via devcontainer feature
if ! command -v poetry &> /dev/null; then
    echo "❌ Poetry not found! This should be installed via devcontainer feature."
    exit 1
fi
poetry --version

# Create MongoDB data directory
mkdir -p /workspaces/data

# Setup .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
    echo "⚠️  Please update .env with your actual credentials"
else
    echo ".env file already exists"
fi

# Set environment variables
echo 'export NODE_OPTIONS=--experimental-worker' >> ~/.bashrc
echo 'export PYMONGOIM__MONGO_VERSION=4.4' >> ~/.bashrc
echo 'export PYMONGOIM__OPERATING_SYSTEM=ubuntu' >> ~/.bashrc

echo "Installing Python dependencies..."
# Ensure Rust is in PATH (needed for libcst build)
if [ -f "$HOME/.cargo/env" ]; then
    source "$HOME/.cargo/env"
    echo "Rust available at: $(which rustc)"
fi

# Install Python dependencies
echo "Running poetry install (this may take a few minutes)..."
poetry install --no-root --with dev

# Verify critical tools are installed
echo "Verifying Python tools installation..."
poetry run ruff --version || { echo "❌ ruff installation failed"; exit 1; }
poetry run pytest --version || { echo "❌ pytest installation failed"; exit 1; }
poetry run pyre --version || { echo "❌ pyre installation failed"; exit 1; }

echo "✅ Development environment setup complete!"
