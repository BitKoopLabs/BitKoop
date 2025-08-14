# syntax=docker/dockerfile:1.6
# Use official Python 3.12 slim image pinned to Debian Bookworm to ensure Playwright deps install reliably
FROM python:3.12-slim-bookworm

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive
ENV PLAYWRIGHT_BROWSERS_PATH=/ms-playwright

# Set work directory
WORKDIR /app

# Install base system dependencies and Node.js (required for npm/npx and Playwright CLI)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libssl-dev \
    pkg-config \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_24.x | bash - \
    && apt-get install -y --no-install-recommends nodejs \
    && rm -rf /var/lib/apt/lists/*

# Install pip and poetry
RUN pip install --upgrade pip

# Pre-copy Node manifests and install Node dependencies with cache
WORKDIR /app/coupon_validation
COPY coupon_validation/package.json coupon_validation/package-lock.json ./
RUN --mount=type=cache,target=/root/.npm npm ci --omit=dev

# Install only Firefox browser and its system deps to reduce time/size
RUN npx playwright install --with-deps firefox

# Copy the rest of the project and install Python package and deps from pyproject
WORKDIR /app
COPY . .
RUN --mount=type=cache,target=/root/.cache/pip pip install .

# Set default environment variables (can be overridden at runtime)
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE ${PORT}

# Use JSON array form for CMD to handle signals properly
CMD ["sh", "-c", "uvicorn subnet_validator.main:app --host $HOST --port $PORT"]