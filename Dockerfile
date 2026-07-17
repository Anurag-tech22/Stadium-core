FROM python:3.11-slim

WORKDIR /app

# Copy and install dependencies in one stage
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application
COPY . .

# Create and run as a secure non-root user
RUN adduser --disabled-password --gecos "" phoenix && chown -R phoenix:phoenix /app
USER phoenix

# Production configuration
ENV PHOENIX_STADIUM_LLM_PROVIDER=mock \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

EXPOSE 8080

# Start Uvicorn dynamically on the port injected by Cloud Run
CMD uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8080}
