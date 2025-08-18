# Use base Python image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies (for ChromaDB, sentence-transformers, etc.)
RUN apt-get update && apt-get install -y \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxrender1 \
    libxext6 \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements.txt
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy all project files
COPY . .

# Expose Flask default port
EXPOSE 5000

# Set environment variables (disable Python buffering for logs)
ENV PYTHONUNBUFFERED=1

# Run Flask app
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]
