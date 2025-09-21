# Use Python 3.11.6 exactly as specified
FROM python:3.11.6-slim

# Set working directory
WORKDIR /app

# Set environment variables for development
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV DJANGO_SETTINGS_MODULE=AteBit.settings

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
        gcc \
        python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project
COPY . .

# Expose port
EXPOSE 8000

# Run development server with auto-reload
CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]
