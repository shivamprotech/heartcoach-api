# syntax=docker/dockerfile:1

# Always target linux/amd64 (for Render, Railway, etc.)
ARG TARGETPLATFORM=linux/amd64

FROM python:3.11-slim AS base

# Set working directory
WORKDIR /app

# Copy dependency files first (for caching)
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the app
COPY . .

# Expose FastAPI port
EXPOSE 8000

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Run Alembic migrations, then start FastAPI
CMD ["bash", "-c", "alembic upgrade head && uvicorn app.main:app --host 0.0.0.0 --port 8000"]
