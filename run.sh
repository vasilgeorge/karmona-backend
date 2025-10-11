#!/bin/bash
# Quick start script for development

export PATH="$HOME/.local/bin:$PATH"

echo "🌙 Starting Karmona Backend..."
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found!"
    echo "Copy .env.example to .env and configure it."
    exit 1
fi

# Run the server
uv run uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
