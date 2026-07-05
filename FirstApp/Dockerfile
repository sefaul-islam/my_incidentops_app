# ==========================================
# Stage 1: Builder — compile dependencies
# ==========================================
FROM python:3.12-slim AS builder

WORKDIR /app

# Install build-time system dependencies (compiler + PG headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

# Build pre-compiled wheels so the final stage never needs gcc
RUN pip wheel --no-cache-dir --no-deps --wheel-dir /app/wheels -r requirements.txt


# ==========================================
# Stage 2: Final — lean production image
# ==========================================
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install ONLY the runtime library for PostgreSQL (no dev headers)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy pre-compiled wheels from builder and install them
COPY --from=builder /app/wheels /wheels
COPY --from=builder /app/requirements.txt .
RUN pip install --no-cache-dir /wheels/*

# Copy application code
COPY . .

EXPOSE 8000

# Use Daphne (ASGI) for WebSocket support
CMD ["daphne", "-b", "0.0.0.0", "-p", "8000", "myproject.asgi:application"]
