# syntax=docker/dockerfile:1

# ---- Build stage: resolve and install Python dependencies ----
FROM python:3.11-slim AS builder

WORKDIR /build

COPY backend/requirements.txt .

RUN pip install --no-cache-dir --no-compile --user -r requirements.txt


# ---- Runtime stage ----
FROM python:3.11-slim AS runtime

# Non-root user the app will run as
RUN useradd --create-home --uid 1000 app

WORKDIR /app

# Installed dependencies only (no pip cache, no build tools)
COPY --from=builder --chown=app:app /root/.local /home/app/.local

# Application code only - no requirements.txt, tests, docs, or .env
COPY --chown=app:app backend/app ./backend/app
COPY --chown=app:app frontend ./frontend

ENV PATH=/home/app/.local/bin:$PATH \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER app

WORKDIR /app/backend

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
