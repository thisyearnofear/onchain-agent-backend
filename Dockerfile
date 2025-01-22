# Use Python 3.10 slim image
FROM python:3.10-slim

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry and Gunicorn
RUN pip install poetry==2.0.1 gunicorn==21.2.0

# Copy Poetry files
COPY pyproject.toml poetry.lock ./

# Configure Poetry
RUN poetry config virtualenvs.create false

# Install dependencies (including root project)
RUN poetry install --without dev --no-interaction --no-ansi

# Copy application code
COPY . .

# Set Python path
ENV PYTHONPATH=/app/src

# Expose port
EXPOSE 5001

# Run the application
CMD ["gunicorn", "--workers=2", "--timeout=120", "--bind=0.0.0.0:$PORT", "--log-level=info", "--worker-class=sync", "--worker-tmp-dir=/dev/shm", "src.agent_backend.index:app"] 