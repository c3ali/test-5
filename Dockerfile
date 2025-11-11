# Use Python base image
FROM python:3.13-slim

# Install Node.js 18.x
RUN apt-get update && apt-get install -y \
    curl \
    gnupg \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set working directory
WORKDIR /app

# Copy package files
COPY package*.json ./

# Install Node.js dependencies
RUN npm install

# Copy Python requirements
COPY requirements.txt ./

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Build frontend
RUN npm run build

# Expose port
EXPOSE 8080

# Start command using shell form to handle $PORT environment variable
CMD uvicorn backend.main:app --host 0.0.0.0 --port ${PORT:-8080}
