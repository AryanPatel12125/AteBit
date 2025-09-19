#!/bin/bash

# Docker entrypoint script for Next.js development
set -e

echo "🚀 Starting AteBit Legal Document Platform Frontend..."

# Handle graceful shutdown
cleanup() {
    echo "🛑 Shutting down gracefully..."
    exit 0
}

trap cleanup SIGTERM SIGINT

# Check if node_modules exists and is populated
if [ ! -d "node_modules" ] || [ -z "$(ls -A node_modules 2>/dev/null)" ]; then
    echo "📦 Installing dependencies..."
    npm ci --no-audit --no-fund
fi

echo "🔧 Node.js version: $(node --version)"
echo "📦 npm version: $(npm --version)"

# Check if we're in development mode
if [ "$NODE_ENV" = "development" ]; then
    echo "🔥 Starting development server with hot reload..."
    echo "🌐 Server will be available at http://0.0.0.0:3000"
    echo "📁 Watching for file changes..."
    
    # Start development server with proper signal handling
    exec npm run dev &
    
    # Wait for the process and handle signals
    wait $!
else
    echo "🏭 Starting production server..."
    exec npm start
fi