#!/bin/bash

# Docker entrypoint script for development
set -e

echo "🚀 Starting AteBit Legal Document Platform Backend..."

# Wait for any dependencies (if needed)
echo "📋 Checking Django configuration..."

# Run Django checks
python manage.py check --deploy || echo "⚠️  Deploy checks failed (expected in development)"

# Run migrations
echo "🔄 Running database migrations..."
python manage.py migrate --noinput

# Collect static files (for development)
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput --clear

# Create superuser if needed (optional)
if [ "$DJANGO_SUPERUSER_USERNAME" ]; then
    echo "👤 Creating superuser..."
    python manage.py createsuperuser --noinput || echo "Superuser already exists"
fi

echo "✅ Setup complete! Starting development server..."

# Start the development server
exec python manage.py runserver 0.0.0.0:8000