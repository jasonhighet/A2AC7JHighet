# Config Service

A centralized configuration management REST API built with **FastAPI** and **PostgreSQL** (no ORM).

## Overview

The Config Service allows applications to store and retrieve named configuration values, scoped per application. It is a simple key-value store exposed over HTTP, designed as a learning vehicle for clean REST API architecture without an ORM layer.

## Tech Stack

| Concern | Technology | Version |
|---|---|---|
| Web framework | FastAPI | 0.116.1 |
| ASGI server | Uvicorn | 0.34.0 |
| Database driver | psycopg2-binary | 2.9.10 |
| ID generation | python-ulid | 3.0.0 |
| Settings | pydantic-settings | 2.7.0 |
| Testing | pytest + httpx | 8.4.1 / 0.28.1 |
| Package manager | uv | — |

## Project Structure

```
config-service/
├── app/
│   ├── main.py               # FastAPI app entry point, router registration
│   ├── config.py             # App settings loaded from environment (.env)
│   ├── database.py           # Raw psycopg2 connection pool
│   ├── exceptions.py         # Custom HTTP exception types
│   ├── applications/         # "Applications" domain (CRUD for app records)
│   │   ├── models.py
│   │   ├── repository.py
│   │   ├── service.py
│   │   ├── router.py
│   │   └── *_test.py
│   └── configurations/       # "Configurations" domain (key-value config entries)
│       ├── models.py
│       ├── repository.py
│       ├── service.py
│       ├── router.py
│       └── *_test.py
├── db/
│   ├── migrations/           # Raw SQL migration files
│   └── run_migrations.py     # Migration runner script
├── conftest.py               # pytest fixtures (DB setup, test client)
├── pyproject.toml            # Project metadata and dependencies
├── Makefile                  # Developer task runner
└── .env.example              # Environment variable template
```

## Getting Started

### 1. Prerequisites

- Python 3.13+
- [`uv`](https://github.com/astral-sh/uv) installed globally
- PostgreSQL running locally on Windows (native install, not Docker)

### 2. Configure Environment

```powershell
Copy-Item .env.example .env
# Edit .env with your PostgreSQL credentials
```

Key variables:

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL connection string for the main database |
| `TEST_DATABASE_URL` | Separate database used by pytest (transactions rolled back after each test) |
| `APP_HOST` | Uvicorn bind host (default: `127.0.0.1`) |
| `APP_PORT` | Uvicorn bind port (default: `8000`) |

### 3. Install Dependencies

```powershell
make install
# equivalent: uv sync --extra dev
```

### 4. Run Migrations

```powershell
make migrate
# equivalent: uv run python db/run_migrations.py
```

### 5. Start Development Server

```powershell
make run
# equivalent: uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

API is then available at `http://127.0.0.1:8000`. Interactive docs at `http://127.0.0.1:8000/docs`.

## Running Tests

```powershell
make test          # Run all tests
make test-cov      # Run tests with coverage report
```

Tests live alongside source files as `*_test.py`. The test suite uses a separate `TEST_DATABASE_URL` database; each test runs inside a transaction that is rolled back on teardown, keeping the test DB clean between runs.

## API Domains

### Applications

Manages the registry of applications that can own configuration entries.

| Method | Path | Description |
|---|---|---|
| `GET` | `/applications` | List all applications |
| `POST` | `/applications` | Create a new application |
| `GET` | `/applications/{id}` | Get an application by ID |
| `DELETE` | `/applications/{id}` | Delete an application |

### Configurations

Manages key-value configuration entries scoped to an application.

| Method | Path | Description |
|---|---|---|
| `GET` | `/applications/{app_id}/configurations` | List all configs for an app |
| `POST` | `/applications/{app_id}/configurations` | Create a config entry |
| `GET` | `/applications/{app_id}/configurations/{id}` | Get a config entry by ID |
| `PUT` | `/applications/{app_id}/configurations/{id}` | Update a config entry |
| `DELETE` | `/applications/{app_id}/configurations/{id}` | Delete a config entry |

## Architecture Notes

- **No ORM** — all database access uses raw SQL via `psycopg2`. Repository classes encapsulate all queries.
- **IDs** — ULIDs are used as primary keys (lexicographically sortable, URL-safe).
- **Layer pattern** — each domain follows: `router → service → repository → database`.
- **Settings** — all configuration is injected via environment variables using `pydantic-settings`; no hardcoded values.
