# Multi-stage build for DBSBM Betting Bot
FROM python:3.11-slim as base

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libffi-dev \
    libssl-dev \
    curl \
    wget \
    git \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY DBSBM/requirements.txt ./DBSBM/
COPY DBSBMWEB/requirements.txt ./DBSBMWEB/

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip wheel setuptools && \
    pip install --no-cache-dir -r DBSBM/requirements.txt && \
    pip install --no-cache-dir -r DBSBMWEB/requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs \
    /app/data/cache \
    /app/static/cache/optimized \
    /app/data/metrics \
    /app/bot/static/cache

# Set environment variables
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV FLASK_ENV=production
ENV FLASK_DEBUG=0

# Create non-root user for security
RUN useradd -m -u 1000 betting-bot && \
    chown -R betting-bot:betting-bot /app

# Switch to non-root user
USER betting-bot

# Expose port
EXPOSE 25594

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:25594/health')" || exit 1

# Start the application
CMD ["python", "DBSBM/bot/main.py"] 