FROM python:3.12-slim

# Don't write .pyc files and don't buffer logs, so `docker logs` is real-time.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Copy requirements first: this layer is cached and only rebuilt
# when dependencies change, not on every code edit.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Run as an unprivileged user: a compromised app can't act as root.
RUN adduser --disabled-password --no-create-home appuser \
    && chown -R appuser /app
USER appuser

# On startup: apply migrations, collect static files for WhiteNoise, then start gunicorn.
# "exec" makes gunicorn the main process (PID 1) so it receives stop signals.
# Railway provides the port in the PORT variable; 8000 is the local default.
CMD sh -c "python manage.py migrate --noinput && \
           python manage.py collectstatic --noinput && \
           exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}"