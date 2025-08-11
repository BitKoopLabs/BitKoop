# Use official Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DEBIAN_FRONTEND=noninteractive

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

# Copy project files
COPY pyproject.toml .
COPY . .

# Install Python project dependencies
RUN pip install --no-cache-dir .

# Install Node.js dependencies for koupons_validator
WORKDIR /app/koupons_validator
RUN npm ci

# Install Playwright system dependencies and browsers
RUN npx playwright install --with-deps

# Return to main app directory
WORKDIR /app

# Set default environment variables (can be overridden at runtime)
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE ${PORT}

# Use JSON array form for CMD to handle signals properly
CMD ["sh", "-c", "uvicorn subnet_validator.main:app --host $HOST --port $PORT"]