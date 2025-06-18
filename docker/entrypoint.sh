#!/bin/bash
set -e

echo "🚀 Starting User Service..."

# Wait for database to be ready
echo "⏳ Waiting for database connection..."

# Start the application
echo "🎯 Starting User Service application..."
exec python -m app.main