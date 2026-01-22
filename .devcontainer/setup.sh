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

    # Install MongoDB and tools
    sudo apt-get update
    sudo apt-get install -y mongodb-org mongodb-org-tools
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
    # Add Rust to PATH for current session
    export PATH="$HOME/.cargo/bin:$PATH"
    # Add Rust to PATH permanently
    echo 'export PATH="$HOME/.cargo/bin:$PATH"' >> ~/.bashrc
    rustc --version
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

echo "Installing Python dependencies..."
# Ensure Rust is in PATH (needed for libcst build)
export PATH="$HOME/.cargo/bin:$PATH"

# Install Python dependencies (this may take several minutes)
if ! poetry install --no-root --with dev; then
    echo "❌ Poetry install failed!"
    echo "This usually means a dependency failed to build."
    echo "Check the output above for errors."
    exit 1
fi

# Verify critical tools are installed
echo ""
echo "Verifying installation..."
if poetry run pytest --version > /dev/null 2>&1; then
    echo "✅ pytest: $(poetry run pytest --version)"
else
    echo "⚠️  pytest not found in virtualenv - dev dependencies may not have installed"
fi

if poetry run ruff --version > /dev/null 2>&1; then
    echo "✅ ruff: $(poetry run ruff --version)"
else
    echo "⚠️  ruff not found in virtualenv"
fi

echo ""
echo "✅ Development environment setup complete!"
