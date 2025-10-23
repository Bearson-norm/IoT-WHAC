# Dockerfile for Local Machine (Raspberry Pi) - Fingerprint Scanner
FROM python:3.9-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    make \
    libffi-dev \
    libssl-dev \
    libbluetooth-dev \
    libusb-1.0-0-dev \
    libudev-dev \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p /app/logs

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Expose port for potential web interface
EXPOSE 8080

# Create a non-root user for security
RUN useradd -m -u 1000 fingerprint && \
    chown -R fingerprint:fingerprint /app
USER fingerprint

# Default command
CMD ["python3", "fingerprint_simple_client.py"]

