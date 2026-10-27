FROM python:3.12-slim

# Don't write .pyc files and don't buffer logs, so `docker logs` is real-time.
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Official working directory. Every next command will be executed on this directory
WORKDIR /app

# Copy requirements first: this layer is cached and only rebuilt
# when dependencies change, not on every code edit.
COPY requirements.txt .
# Don't install temporary installation packages, keeps the images slim
RUN pip install --no-cache-dir -r requirements.txt

# After installing dependencies, copy the whole source code (Django project) inside the container
COPY . .

# Run as an unprivileged user: a compromised app can't act as root.
# Creating a fake user without priviliges (does not have root privileges) and containers uses it by default
# Important for security reasons, if a hacker manages to enter the system, they'll have "appuser" privileges, not root privileges
RUN adduser --disabled-password --no-create-home appuser \
    && chown -R appuser /app
USER appuser


# Makes migrations on the database without requiring ok input from user
# Gathers all static data (CSS, images) so that WhiteNoise can use it
# The final exec command starts the Gunicorn production server, replacing the shell process and becoming the main process (PID 1) 
# ${PORT:-8000} important for Railway. Gunicorn dynamically listens to the port provided by the cloud service (contained in the env var PORT)
# If not set, the env var PORT has default value 8000 (essential for my local tests)
CMD sh -c "python manage.py migrate --noinput && \
           python manage.py collectstatic --noinput && \
           exec gunicorn config.wsgi:application --bind 0.0.0.0:${PORT:-8000}"