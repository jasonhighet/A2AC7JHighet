# Config Service Admin UI

Web-based Admin Interface for managing the **Config Service** — built with native Web Components, TypeScript 5, and Vanilla CSS.

---

## Prerequisites

| Tool | Minimum Version |
|------|----------------|
| Node.js | 20.x |
| pnpm | 9.x |

---

## Setup (PowerShell)

```powershell
# Install dependencies
pnpm install

# Install Playwright browsers (first time only)
pnpm exec playwright install chromium
```

---

## Development

```powershell
# 1. Start the backend API (from config-service directory)
uvicorn app.main:app --host 127.0.0.1 --port 8000

# 2. Start the UI dev server (from ui/ directory)
pnpm dev
```

Open `http://localhost:3000` in your browser.

> **Vite Proxy**: In development, all `/api/*` requests are proxied to `http://localhost:8000` by `vite.config.ts`. This means the browser never makes a cross-origin request during local development.

> **CORS**: In production (or when not using the Vite proxy), the FastAPI backend must allow `http://localhost:3000`. This is already configured in `config-service/app/main.py` via `CORSMiddleware`.

---

## Tests

```powershell
# Unit tests (Vitest — no backend required)
pnpm test:unit

# Unit tests with coverage report
pnpm test:unit:coverage

# E2E tests (Playwright — backend must be running on port 8000)
pnpm test:e2e

# E2E tests with interactive UI
pnpm test:e2e:ui
```

---

## Build

```powershell
pnpm build
# Output written to dist/
```

---

## Architecture

| Layer | Technology |
|-------|-----------|
| Components | Native Web Components + Shadow DOM |
| State | `AppStore` singleton extending `EventTarget` |
| HTTP | `fetch` API via typed `ApiClient` |
| Styles | CSS Custom Properties (`tokens.css`) |
| Bundler | Vite 5 |
| Unit tests | Vitest 2 + jsdom |
| E2E tests | Playwright 1.47 |

---

## Known Limitations / Future Improvements

- **Configuration listing is a waterfall**: `GET /applications/{id}` returns `configuration_ids[]`, which are then fetched individually. A future backend endpoint (`GET /configurations?application_id=X`) will replace this.
- **No authentication**: The API is open. Auth will be added in a future phase; a stub hook is ready in `src/api/client.ts`.
