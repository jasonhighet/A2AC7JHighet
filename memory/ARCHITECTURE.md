# Project Architecture

## Service Boundaries
The Config Service is logically divided into two primary domains:
- **Applications Management**: Manages the metadata for consumer applications (naming, descriptions, etc.). Located in `app/applications/`.
- **Configuration Management**: Manages the actual configuration variables (keys, values, environments) scoped to specific applications. Located in `app/configurations/`.

## Data Management & Migrations
- **Custom Migration System**: Instead of Alembic, the project uses a custom Python script `db/run_migrations.py`.
- **Plain SQL**: Migrations are written in plain `.sql` files located in `db/migrations/`.
- **Execution**: Run migrations via `uv run python db/run_migrations.py`.

## Layered Organization
- **Routers**: FastAPI routers defining the API contract.
- **Logic/Services**: Domain-specific logic (currently integrated into routers or helper modules).
- **Database Access**: Direct SQL execution within database utility wrappers.

## Error Handling
- **Domain Exceptions**: Custom exceptions defined in `app/exceptions.py`.
- **Global Handlers**: Mapped to consistent JSON responses in `app/main.py` via FastAPI exception handlers.
