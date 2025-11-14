FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    ffmpeg \
    wget \
    curl \
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

# Expose port (if needed for web interface)
EXPOSE 8080

# Start the bot
CMD ["python", "main.py"]
