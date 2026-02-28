# Technical Stack & Constraints

## Strict Constraints
- **Strictly No ORM**: All database interactions must use raw SQL via `psycopg2-binary`. Do not introduce SQLAlchemy, Tortoise, or any other ORM.
- **Windows-Native Environment**: All development, testing, and deployment assume a native Windows environment with PowerShell. 
  - **No Docker**: Do not use Docker or Docker Compose.
  - **No WSL/Linux**: Do not assume Linux-specific tools or paths.
- **Package Management**: Use `uv` for all dependency management and virtual environment handling.

## Language and Framework
- **Python 3.13.5+**: High-standard Python code using the latest features (type hints, f-strings, etc.).
- **FastAPI 0.116.1**: The core web framework for building the REST API.

## Database
- **PostgreSQL**: Native Windows installation.
- **Connection Handling**: Managed via a custom database utility in `app/database.py`.

## Utilities
- **ULID**: Use Universally Unique Lexicographically Sortable Identifiers for primary keys (via `python-ulid`).
- **Pydantic**: Use for request/response validation and configuration management (`pydantic-settings`).

## UI & Client Libraries
- **Vanilla TypeScript**: Shared libraries (like `config-client`) must be framework-agnostic.
- **Native Fetch**: Use the browser's native `fetch` API; avoid `axios` or other wrappers to keep dependencies minimal.
- **Bundling**: Use `tsup` for high-performance library bundling (CJS/ESM/DTS).
- **Testing**: Standardize on `vitest` for all TypeScript/UI-related unit testing.

## See Also
- [`memory/ENV_SCRIPTS.md`](./ENV_SCRIPTS.md) — Environment variables, `uv` commands, Makefile targets, and `pnpm` scripts for all services.
