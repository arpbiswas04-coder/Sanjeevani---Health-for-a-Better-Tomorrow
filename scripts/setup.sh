#!/usr/bin/env bash
set -e

echo "=== Setting up Sanjeevani Grid Development Environment ==="

# Check .env
if [ ! -f .env ]; then
    echo "Creating .env from .env.example..."
    cp .env.example .env
else
    echo ".env already exists, skipping copy."
fi

echo "Verifying environment prerequisites..."
command -v node >/dev/null 2>&1 && echo "✓ Node.js found: $(node -v)" || echo "✗ Node.js not found"
command -v python3 >/dev/null 2>&1 && echo "✓ Python3 found: $(python3 --version)" || echo "✗ Python3 not found"
command -v docker >/dev/null 2>&1 && echo "✓ Docker found: $(docker --version)" || echo "! Docker not found (optional for local standalone dev)"

echo "Done! To start services with Docker Compose, run:"
echo "  docker compose up --build"
