#!/bin/bash
set -e

echo "=== Starting application setup ==="

# Check if Node.js is available
if command -v node &> /dev/null; then
    echo "Node.js is available: $(node --version)"

    # Check if npm is available
    if command -v npm &> /dev/null; then
        echo "npm is available: $(npm --version)"

        # Install dependencies if node_modules doesn't exist
        if [ ! -d "node_modules" ]; then
            echo "Installing npm dependencies..."
            npm install
        else
            echo "node_modules already exists, skipping npm install"
        fi

        # Build frontend if dist doesn't exist
        if [ ! -d "dist" ] || [ ! -f "dist/index.html" ]; then
            echo "Building frontend..."
            npm run build
            echo "Frontend build complete"
        else
            echo "Frontend already built, skipping build"
        fi
    else
        echo "WARNING: npm not available, skipping frontend build"
    fi
else
    echo "WARNING: Node.js not available, skipping frontend build"
fi

# Check if dist exists
if [ -d "dist" ]; then
    echo "SUCCESS: dist directory exists"
    ls -la dist/
else
    echo "WARNING: dist directory not found - frontend will not be available"
fi

echo "=== Starting uvicorn ==="
# Start the FastAPI application
exec uvicorn backend.main:app --host 0.0.0.0 --port $PORT
