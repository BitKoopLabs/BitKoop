# Use official Python 3.12 slim image
FROM python:3.12-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies including Node.js and Playwright browser dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    build-essential \
    git \
    libssl-dev \
    pkg-config \
    curl \
    gnupg \
    # Install Node.js 24 (latest LTS)
    && curl -fsSL https://deb.nodesource.com/setup_24.x | DEBIAN_FRONTEND=noninteractive bash - \
    && DEBIAN_FRONTEND=noninteractive apt-get install -y nodejs \
    # Playwright browser dependencies
    && apt-get install -y --no-install-recommends \
    libxcb-shm0 \
    libx11-xcb1 \
    libx11-6 \
    libxcb1 \
    libxext6 \
    libxrandr2 \
    libxcomposite1 \
    libxcursor1 \
    libxdamage1 \
    libxfixes3 \
    libxi6 \
    libgtk-3-0 \
    libgdk-pixbuf-2.0-0 \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libatk1.0-0 \
    libcairo2 \
    libcairo-gobject2 \
    libglib2.0-0 \
    libxrender1 \
    libasound2 \
    libfreetype6 \
    libfontconfig1 \
    libdbus-1-3 \
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
RUN npm install

# Install Playwright browsers
RUN npx playwright install

# Return to main app directory
WORKDIR /app

# Set default environment variables (can be overridden at runtime)
ENV HOST=0.0.0.0
ENV PORT=8000

EXPOSE ${PORT}

# Use JSON array form for CMD to handle signals properly
CMD ["sh", "-c", "uvicorn subnet_validator.main:app --host $HOST --port $PORT"]