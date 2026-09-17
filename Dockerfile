# Official Microsoft Playwright container with Chromium pre-configured
FROM mcr.microsoft.com/playwright/python:v1.41.0-jammy

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    DEBIAN_FRONTEND=noninteractive \
    HEADLESS_BROWSER=true

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    git \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create persistent data directories
RUN mkdir -p /app/data/resumes /app/data/screenshots

# Ensure playwright browsers are installed
RUN playwright install chromium

# Run bot
CMD ["python", "main.py"]
