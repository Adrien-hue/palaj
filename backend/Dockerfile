FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

WORKDIR /app

# Deps système minimales
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
  && rm -rf /var/lib/apt/lists/*

# Installer les deps Python
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copier le code nécessaire au runtime
COPY backend /app/backend
COPY core /app/core
COPY db /app/db
COPY alembic /app/alembic
COPY alembic.ini /app/alembic.ini

EXPOSE 8000

CMD ["bash", "-lc", "python -m backend.scripts.wait_for_db && python -m uvicorn backend.app.main:app --host 0.0.0.0 --port 8000"]