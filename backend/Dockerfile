FROM python:3.12-slim

WORKDIR /app

COPY backend ./backend
COPY backend/requirements-bot.txt ./backend/requirements-bot.txt

RUN pip install --no-cache-dir \
  "fastapi>=0.115.0" \
  "uvicorn>=0.30.0" \
  "pydantic>=2.8.0" \
  "python-jose[cryptography]>=3.3.0" \
  "email-validator>=2.2.0" \
  "sqlalchemy>=2.0.36" \
  "psycopg[binary]>=3.2.3" \
  "argon2-cffi>=23.1.0" \
  "alembic>=1.13.0" \
  && pip install --no-cache-dir -r backend/requirements-bot.txt

EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=10 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/healthz', timeout=2).read()" || exit 1

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
