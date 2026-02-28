# Environment & Developer Scripts

This file is the authoritative reference for running the project locally.

---

## Target Environment: Local Windows Development

This project targets **one environment: a native Windows developer machine**.

| Property | Value |
|---|---|
| OS | Windows (native) |
| Shell | PowerShell |
| Python runtime | Python 3.13+ via `uv` |
| Node runtime | Node.js (LTS) via `pnpm@10.29.3` |
| Database | PostgreSQL v17 (native Windows install) |
| Containerisation | **None** — no Docker, no WSL, no Linux paths |

> There is no staging or production environment defined for this course project. All commands and paths assume a local Windows context.

---

## Environment Variables

The `config-service` reads configuration from a `.env` file in its root directory, loaded via `pydantic-settings` (`app/config.py`).

Create `config-service/.env` with the following variables:

```env
# Required
DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/hypr_config

# Optional — leave empty to skip DB-dependent tests
TEST_DATABASE_URL=postgresql://postgres:yourpassword@localhost:5432/hypr_config_test

# Optional — defaults shown
APP_HOST=127.0.0.1
APP_PORT=8000
```

| Variable | Required | Default | Description |
|---|---|---|---|
| `DATABASE_URL` | ✅ | — | PostgreSQL v17 connection string |
| `TEST_DATABASE_URL` | No | `""` | Separate test database; empty string disables DB tests |
| `APP_HOST` | No | `127.0.0.1` | Uvicorn bind host |
| `APP_PORT` | No | `8000` | Uvicorn bind port |

> **Note:** PostgreSQL v17 must be installed natively on Windows. The database and user must be created manually before running migrations.

---

## Python Backend (`config-service/`)

All commands run from the `config-service/` directory. Requires `uv` to be installed.

### `uv` Commands (canonical)

```powershell
# Install runtime + dev dependencies
uv sync --extra dev

# Start the development server with hot-reload
uv run uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload

# Apply pending database migrations
uv run python db/run_migrations.py

# Run the full test suite
uv run pytest

# Run tests with coverage report
uv run pytest --cov=app --cov-report=term-missing
```

> **Assistant rule:** Use `uv run python -m <module>` syntax for Python module invocations (e.g., `uv run python -m pytest`). The `uv run python` prefix ensures the correct virtual environment is always used — never call `python` or `pytest` directly.

### Makefile Targets

A `Makefile` is provided as a convenience wrapper. Requires `make` to be available on Windows (e.g., via [GnuWin32](http://gnuwin32.sourceforge.net/) or `choco install make`).

| Target | Equivalent `uv` Command | Description |
|---|---|---|
| `make install` | `uv sync --extra dev` | Install all dependencies |
| `make run` | `uv run uvicorn app.main:app ...` | Start the dev server |
| `make migrate` | `uv run python db/run_migrations.py` | Apply pending migrations |
| `make test` | `uv run pytest` | Run the full test suite |
| `make test-cov` | `uv run pytest --cov=app --cov-report=term-missing` | Tests with coverage |
| `make help` | — | Print available targets |

The Makefile is fully permitted for day-to-day use. The raw `uv run` commands are always acceptable equivalents.

### Going Off-Script

Use the raw `uv run` commands (rather than `make` targets) when:

- **The Makefile has no target for what you need** — e.g. running a single test file (`uv run pytest app/applications/router_test.py -v`) or passing extra flags.
- **Debugging a specific case** — e.g. `uv run pytest -k test_create_application --pdb` to drop into the debugger.
- **`make` is not installed** on the machine — the raw `uv run` commands are always the ground truth.
- **The assistant is generating a command** — always emit the full `uv run ...` form so it is explicit and portable.

Never invent new Makefile targets mid-task; add them to the `Makefile` intentionally and document them here.

---

## TypeScript UI (`ui/`)

### Admin UI (`ui/`)

Uses `pnpm@10.29.3` (pinned via `packageManager` in `package.json`). Run from the `ui/` directory.

```powershell
# Install dependencies
pnpm install

# Start the dev server (http://localhost:3000)
pnpm dev

# Type-check without emitting
pnpm run typecheck

# Run unit tests (single pass)
pnpm run test:unit

# Run unit tests with coverage
pnpm run test:unit:coverage

# Run unit tests in watch mode
pnpm run test:unit:watch

# Run end-to-end tests (Playwright)
pnpm run test:e2e

# Run e2e tests with Playwright UI
pnpm run test:e2e:ui

# Production build
pnpm build
```

### Config Client Library (`ui/packages/config-client/`)

Run from the `ui/packages/config-client/` directory.

```powershell
# Install dependencies
pnpm install

# Build the library (CJS + ESM + type declarations)
pnpm run build

# Run unit tests
pnpm test

# Type-check without emitting
pnpm run typecheck
```

---

## Assistant Rules

- **Do not use Docker, WSL, or Linux-specific commands** (e.g., no `./scripts/run.sh`, no `bash`).
- **Always use `uv run`** to invoke Python — never bare `python`, `pip`, or `pytest`.
- **Prefer `uv run python -m <module>`** syntax for module-style invocations.
- **Always specify the working directory** in any instructions (e.g., "run from `config-service/`").
- **Makefile targets are permitted** — use `make <target>` as a shorthand where appropriate.
