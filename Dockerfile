FROM python:3.11-slim

# Accept build arguments from .env
ARG WORKDIR_PATH
ARG PORT

# Set working directory
WORKDIR ${WORKDIR_PATH}

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create storage directories
RUN mkdir -p storage/uploads storage/edited storage/temp

# Expose port
EXPOSE ${PORT}

# Default command (can be overridden in docker-compose)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
