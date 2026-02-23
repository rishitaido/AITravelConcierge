# =============================================================
# Dockerfile — Multi-stage build for the Flask travel platform
# =============================================================
#
# WHY MULTI-STAGE?
# We split the build into two stages so the final image is small
# and doesn't contain compilers, header files, or build tools.
#   Stage 1 ("builder") — install OS packages + Python deps
#   Stage 2 ("final")   — copy only the built venv + app code
#
# HOW TO USE:
#   docker build -t airports-ai:local .
#   docker run --rm -p 8080:8080 --env-file .env airports-ai:local
# =============================================================

# syntax=docker/dockerfile:1.4

# ---------- Base image (shared by both stages) ----------
FROM python:3.11.11-slim AS base
WORKDIR /app
ENV PYTHONUNBUFFERED=1


# ---------- Stage 1: Builder ----------
# Installs OS-level build tools and Python packages.
# This stage is thrown away — none of these compilers end up
# in the final image.
FROM base AS builder

# OS packages needed to compile Python C extensions (e.g. psycopg2)
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

# Copy requirements first (better layer caching — only re-installs
# if requirements.txt changes, not on every code edit)
COPY --link requirements.txt .

# Create a virtual environment and install Python dependencies
RUN --mount=type=cache,target=/root/.cache/pip \
    python -m venv .venv && \
    .venv/bin/pip install --upgrade pip setuptools wheel && \
    .venv/bin/pip install --no-cache-dir -r requirements.txt

# Now copy the rest of the app code
COPY --link . .


# ---------- Stage 2: Final (production) image ----------
# Starts from the slim base again — no compilers, no build tools.
FROM base AS final

# Create a non-root user (security best practice — if the app
# gets compromised, the attacker can't modify system files)
RUN addgroup --system appgroup && \
    adduser --system --ingroup appgroup appuser

# Copy the built venv and app code from the builder stage
COPY --from=builder /app/.venv    /app/.venv
COPY --from=builder /app          /app
RUN chown -R appuser:appgroup /app

# Put the venv's Python on PATH so `python` resolves to the venv
ENV PATH="/app/.venv/bin:$PATH"

EXPOSE 8080

# Run as the non-root user
USER appuser

# Start the Flask app
CMD ["python", "app.py"]