#!/bin/bash
set -e

# Run Alembic migrations
alembic upgrade head

# Start the FastAPI app
uvicorn subnet_validator.main:app --host "${HOST:-0.0.0.0}" --port "${PORT:-8000}"