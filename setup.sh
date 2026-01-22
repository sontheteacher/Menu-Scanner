#!/bin/bash

# Setup script for local development

set -e

echo "Setting up Menu Scanner local development environment..."

# Check for required tools
command -v docker >/dev/null 2>&1 || { echo "Error: docker is required but not installed."; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Error: docker-compose is required but not installed."; exit 1; }

# Create credentials directory
mkdir -p credentials

# Copy environment file
if [ ! -f .env ]; then
    cp .env.example .env
    echo "Created .env file from .env.example"
    echo "Please update .env with your configuration"
fi

# Create empty __init__.py files for Python packages
touch services/menu-service/src/__init__.py
touch services/menu-service/src/processors/__init__.py
touch services/image-service/src/__init__.py

echo ""
echo "==============================================="
echo "Setup complete!"
echo "==============================================="
echo ""
echo "Next steps:"
echo "1. Update .env file with your configuration"
echo "2. For GCP integration, place service-account.json in credentials/"
echo "3. Start services with: docker-compose up -d"
echo "4. Access API at: http://localhost:8080"
echo "5. View API docs at: http://localhost:8080/api-docs"
echo ""
