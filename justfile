# wfs task runner. Run `just` to list recipes.
# https://github.com/casey/just

# Show available recipes.
default:
    @just --list

# One-time setup: create the venv and install Python (+ worker) deps.
setup:
    #!/usr/bin/env bash
    set -euo pipefail
    if command -v uv >/dev/null 2>&1; then
        uv venv .venv
        source .venv/bin/activate
        uv pip install -e ".[dev]"
    else
        python3 -m venv .venv
        source .venv/bin/activate
        pip install --upgrade pip
        pip install -e ".[dev]"
    fi
    if command -v npm >/dev/null 2>&1; then npm install; else echo "npm not found — skipping worker deps"; fi
    @echo "Done. Run 'direnv allow' to auto-activate the venv on cd."

# Run the API locally with hot reload (:8000).
run:
    uvicorn wfs.main:app --reload --host 0.0.0.0 --port 8000

# Run the test suite (pass extra args, e.g. `just test -k health`).
test *args:
    pytest {{args}}

# Lint + format check with ruff.
lint:
    ruff check .
    ruff format --check .

# Auto-fix lint issues and format the code.
fmt:
    ruff check --fix .
    ruff format .

# Build the container image locally (sanity check before deploy).
build:
    docker build -t wfs:local .

# Deploy to Cloudflare (needs wrangler auth).
deploy:
    npx wrangler deploy
