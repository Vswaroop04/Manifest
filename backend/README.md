# Backend — Django REST API

Django 5 + DRF API that geocodes addresses, calls the ORS routing engine, runs the HOS calculator, and persists trips to Postgres.

---

## Stack

- **Runtime**: Python 3.12, Django 5.1, Django REST Framework 3.15
- **Server**: Gunicorn
- **Database**: PostgreSQL 16 (via `dj-database-url` + `psycopg2`)
- **Cache**: Redis 7 (via `django-redis`)
- **Schema**: drf-spectacular (OpenAPI 3)
- **Linting**: Ruff, Pyright

---

## Setup

### 1. Start Postgres + Redis

```bash
docker compose up -d
```

### 2. Create virtualenv and install deps

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Configure environment

```bash
cp .env.example .env
```

Edit `.env`:

```bash
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/manifest_dev
REDIS_URL=redis://localhost:6379/0
ORS_API_KEY=your-ors-key          # free at openrouteservice.org
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

### 4. Migrate and run

```bash
python manage.py migrate
python manage.py runserver
```

API base: `http://localhost:8000`
Swagger UI: `http://localhost:8000/api/schema/swagger/`

---

## API reference

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health/` | Health check |
| POST | `/api/trips/plan/` | Plan a new trip |
| GET | `/api/trips/` | List past trips (paginated, newest first) |
| GET | `/api/trips/{id}/` | Get full trip detail by UUID |
| GET | `/api/geocode/?q={query}` | Address autocomplete suggestions |

### POST /api/trips/plan/

Request body:

```json
{
  "current_location": "Chicago, IL",
  "pickup_location": "Memphis, TN",
  "dropoff_location": "Dallas, TX",
  "cycle_hours_used": 24.5,
  "departure_time": "2026-05-20T08:00:00"
}
```

Response includes: route geometry, all events (rest/break/fuel/pickup/dropoff), per-day log sheet segments, and trip summary.

---

## Project layout

```
backend/
├── apps/trips/
│   ├── models.py              # Trip, TripEvent, DayLog models
│   ├── views.py               # API view functions
│   ├── serializers.py         # DRF serializers (request + response)
│   ├── urls.py                # URL routing
│   ├── middleware.py          # Request logging
│   ├── services/
│   │   ├── geocoding.py       # Photon + Nominatim geocoder
│   │   ├── route_service.py   # ORS + OSRM routing
│   │   ├── hos_calculator.py  # FMCSA HOS rule engine
│   │   ├── log_sheet_builder.py  # Per-day segment builder
│   │   └── trip_planner.py    # Orchestrates geocode → route → HOS → save
│   └── utils/cache.py         # Redis cache helpers
└── config/
    ├── settings/
    │   ├── base.py            # All settings, env-driven
    │   ├── development.py
    │   └── production.py
    └── urls.py
```

---

## Environment variables

| Variable | Default | Notes |
|----------|---------|-------|
| `SECRET_KEY` | dev key | Change in production |
| `DATABASE_URL` | local postgres | Full connection string |
| `REDIS_URL` | local redis | Full connection string |
| `ORS_API_KEY` | — | Required for truck routing |
| `ALLOWED_HOSTS` | `localhost,127.0.0.1` | Comma-separated |
| `CORS_ALLOWED_ORIGINS` | `http://localhost:5173` | Comma-separated |
| `PHOTON_URL` | Komoot hosted | Override if self-hosting |
| `NOMINATIM_URL` | OSM hosted | Override if self-hosting |
| `ORS_URL` | ORS hosted | Override if self-hosting |
| `OSRM_URL` | OSRM demo | Override if self-hosting |

---

## Tests

```bash
pytest
pytest tests/test_hos_calculator.py    # HOS rule unit tests
pytest tests/test_log_sheet_builder.py # Log sheet segment tests
```

---

## Code quality

```bash
ruff check .          # lint
ruff format .         # format
pyright               # type check
```

---

## Deploying to Railway

1. Push the `backend/` directory to a GitHub repo (or use the monorepo root)
2. Create a new Railway project, connect the repo
3. Add a **Postgres** plugin and a **Redis** plugin from the Railway dashboard
4. Set these environment variables in Railway:
   - `SECRET_KEY`
   - `ORS_API_KEY`
   - `ALLOWED_HOSTS` — set to your Railway app domain
   - `CORS_ALLOWED_ORIGINS` — set to your frontend URL
   - `DATABASE_URL` and `REDIS_URL` are injected automatically by Railway plugins
5. Set the start command: `gunicorn config.wsgi:application --bind 0.0.0.0:$PORT`
6. Run migrations via Railway's one-off command: `python manage.py migrate`

The app has no static files served by Django (frontend is separate), so no `collectstatic` step is needed.
