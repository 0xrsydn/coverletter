FROM python:3.9-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    NODE_VERSION=18.x

# Install system dependencies and Node.js
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    gnupg \
    ca-certificates \
    && curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION} | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Copy UV directly from the official image
COPY --from=ghcr.io/astral-sh/uv:0.6.16 /uv /bin/uv

# Create and activate a virtual environment
RUN uv venv /opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy package files and install Node dependencies first (for better caching)
COPY package*.json ./
RUN npm install

# Copy Python requirements and install dependencies
COPY requirements.txt .
RUN uv pip install -r requirements.txt

# Copy application code
COPY . .

# Build CSS for production
RUN npm run build:css:prod

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Command to run the application in production
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"] 