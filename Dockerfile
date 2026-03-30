# Stage 1: Build Dependencies
FROM python:3.11-slim as builder

# Set work directory
WORKDIR /app

# Prevent python from writing pyc files to disc
ENV PYTHONDONTWRITEBYTECODE 1
# Prevent python from buffering stdout and stderr
ENV PYTHONUNBUFFERED 1

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt .
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt

# Stage 2: Final Production Image
FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Install libpq for psycopg2
RUN apt-get update && \
    apt-get install -y --no-install-recommends libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Copy wheels from builder and install
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache /wheels/*

# Copy the app files into the container
COPY ./app ./app
COPY ./alembic.ini .
COPY ./gunicorn_conf.py .

# Create a non-root user and switch to it
RUN addgroup --system appgroup && adduser --system --group appuser
RUN chown -R appuser:appgroup /app
USER appuser

# Expose the standard port
EXPOSE 8000

# Start command uses Gunicorn to bridge to Uvicorn, as per Raman Bazhanau's production guide
# Runs alembic migrations dynamically on boot
CMD ["bash", "-c", "alembic upgrade head && gunicorn -c gunicorn_conf.py app.main:app"]
