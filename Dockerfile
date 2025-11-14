FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
    libmagic1 \
    file \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create necessary directories
RUN mkdir -p temp logs

# Environment variables
ENV PYTHONPATH=/app
ENV TEMP_DIR=/app/temp

# Use a simple health check that works with Pyrogram
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD ps aux | grep python | grep -v grep || exit 1

# Start the bot
CMD ["python", "main.py"]
