# Asset Tracker

A web application for tracking the assets of a company or any organization. Built with Django, PostgreSQL and Docker.


## Features

- Asset registry with an auto-generated tag, category, location, status, serial number, purchase data and notes
- Hierarchical locations (e.g. Campus > Building > Floor > Room)
- Full history of every asset: creation, moves, status changes and assignments, with the user who made them
- Role-based access control: Manager (full access) and Authorized User (view assets and update operational fields only)
- Search, filters and pagination on the asset list
- Dashboard with an inventory overview by location, status and category, plus recent activity


## Tech stack

- Python 3.12, Django
- PostgreSQL 16
- HTML, CSS
- Docker and Docker Compose
- Gunicorn and WhiteNoise for production


## Getting started

Requirements: [Docker Desktop](https://www.docker.com/products/docker-desktop/) and Git.

1. Clone the repository:

   ```bash
   git clone https://github.com/freddyGut/asset-tracker.git
   cd asset-tracker
   ```

2. Create your environment file and set a `SECRET_KEY` (see below):

   ```bash
   cp .env.example .env        # on Windows cmd: copy .env.example .env
   ```

3. Build and start the containers (migrations run automatically):

   ```bash
   docker compose up --build
   ```

4. In a second terminal, create the user groups and a superuser:

   ```bash
   docker compose exec web python manage.py createsuperuser
   ```

5. Open http://localhost:8000 and log in.

To stop the application run `docker compose down`.


## Environment variables

Defined in `.env` (see `.env.example`):

| Variable | Description |
|---|---|
| `DEBUG` | `True` for local development, `False` in production |
| `SECRET_KEY` | Long random string used by Django for signing. Required when `DEBUG=False` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed host names |
| `CSRF_TRUSTED_ORIGINS` | Comma-separated list of trusted origins (HTTPS URLs), needed in production |
| `DATABASE_URL` | PostgreSQL connection URL. Falls back to SQLite if unset |

A random secret key can be generated with:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```


## Roles

Roles are Django groups, created by `python manage.py setup_roles`. Assign users to a group from the admin panel (`/admin/`).

| Role | Permissions |
|---|---|
| Manager | Create, edit and delete assets, categories and locations; view history |
| Authorized User | View assets; update status, location, assignee and notes only |


## Project structure

```
config/      project settings and root URLs
accounts/    custom user model and authentication
assets/      assets, categories, locations, history and roles setup
dashboard/   inventory overview
templates/   shared templates (base, error pages)
static/      shared CSS
```


## Deployment

The `Dockerfile` is production-ready (Gunicorn, WhiteNoise, unprivileged user) and is used as-is on [Railway](https://railway.com): set the environment variables above and attach a PostgreSQL database.