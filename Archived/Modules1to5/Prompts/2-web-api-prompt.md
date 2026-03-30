I need you to create a **comprehensive implementation plan** for a REST Web API called the **Config Service**. Please strictly adhere to the following technical specifications — **do not introduce any additional dependencies without my explicit approval**. If any details are unclear or you need more information, please ask before proceeding.

---

## Technical Specifications: Config Service

**Tech Stack:**
- **Language:** Python 3.13.5 (managed via `uv`)
- **Web Framework:** FastAPI 0.116.1
- **ASGI Server:** uvicorn 0.34.0 (bare — **no** `[standard]` extra; avoids `uvloop` which is unsupported on Windows)
- **Database:** PostgreSQL (native Windows install — no Docker)
- **Database Adapter:** psycopg2-binary 2.9.10 (strictly **no ORM** — use the binary wheel; no C compiler or PostgreSQL dev headers required on Windows)
- **Developer Tools:** `uv` (for virtual environment and dependency management), `Makefile` (standard Windows `make`)

---

## Service Purpose

A centralized configuration management service. It allows applications to fetch their configuration data (key-value pairs) at runtime via an API.

---

## API Endpoints

All routes are prefixed with `/api/v1`.

**Applications:**
- `POST /applications` — Create an application
- `PUT /applications/{id}` — Update an application
- `GET /applications/{id}` — Get an application by ID
- `GET /applications` — List all applications

**Configurations:**
- `POST /configurations` — Create a configuration
- `PUT /configurations/{id}` — Update a configuration
- `GET /configurations/{id}` — Get a configuration by ID

---

## Data Model

**Application:**
- `id` — ULID (primary key)
- `name` — string, unique
- `comments` — string (optional)

**Configuration:**
- `id` — ULID (primary key)
- `application_id` — ULID (foreign key → applications.id)
- `name` — string
- `comments` — string (optional)
- `config` — JSONB dictionary of name/value pairs

---

## Authentication

**None at this time.** Authentication is a future feature — do not plan for or implement it.

---

## Project Location

Create the service inside a subdirectory named `config-service/` in the current working directory.

---

## Testing

- **Framework:** pytest 8.4.1 with httpx 0.28.1
- **Convention:** Every code file must have a co-located `_test.py` file in the same folder
- **Coverage Target:** 80% for core scenarios

---

## What the Plan Should Include

1. **Dependencies** — List all required packages with exact versions (no extras unless I approve them).
2. **File & Folder Structure** — A clear project layout with descriptions of each file/directory's purpose.
3. **Architectural Patterns** — Describe the patterns you'll use (e.g. repository pattern, service layer, routing conventions, error handling strategy).
4. **Database Setup** — How raw SQL with psycopg2 will be structured (connection management, query helpers, migrations approach).
5. **FastAPI Setup** — Router organization, request/response models (using Pydantic), and any middleware.
6. **Developer Experience** — How `uv` and `Makefile` targets will be set up for common tasks (run, test, lint, etc.).


