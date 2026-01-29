# syntax=docker/dockerfile:1.4

############################################
#  Base image (common to builder & final) #
############################################
FROM python:3.11-slim AS base

# Set a working directory
WORKDIR /app

# Ensure Python outputs logs directly to the console
ENV PYTHONUNBUFFERED=1

############################################
#             Builder stage                #
############################################
FROM base AS builder

# Install OS deps (cached) for wheels, psycopg2, etc.
RUN --mount=type=cache,target=/var/cache/apt \
    apt-get update && \
    apt-get install -y --no-install-recommends \
      build-essential \
      gcc \
      libpq-dev \
      python3-dev \
      libffi-dev \
      libssl-dev \
      git && \
    rm -rf /var/lib/apt/lists/*

# Copy requirements for better layer caching
COPY --link requirements.txt .

# Create a venv and install Python deps (cached)
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv .venv && \
    .venv/bin/pip install --upgrade pip setuptools wheel && \
    .venv/bin/pip install --no-cache-dir -r requirements.txt

# Copy in your application code
COPY --link . .

############################################
#              Final stage                 #
############################################
FROM base AS final

# Create a non-root user
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

# Copy in the installed venv and app code from builder

COPY --from=builder /app/.venv    /app/.venv
COPY --from=builder /app          /app
RUN chown -R appuser:appgroup /app

# Use the venv’s python/pip by default
ENV PATH="/app/.venv/bin:$PATH"

# Expose your Flask port
EXPOSE 8080

# Switch to non-root
USER appuser

# Launch the app
CMD ["python", "app.py"]