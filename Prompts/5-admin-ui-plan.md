# Admin UI — Implementation Plan

This document outlines the architecture and delivery strategy for a web-based Admin UI that consumes the **Config Service REST API** (`http://localhost:8000/api/v1`). The UI is built with **native Web Components**, **TypeScript 5**, and **Vanilla CSS** — no external UI frameworks.

> [!IMPORTANT]
> **Environment**: This is a **native Windows** project. All shell examples use PowerShell-compatible syntax. Do not use WSL, Linux paths, or Docker-specific commands.

---

## API Surface (from `config-service`)

| Method | Path | Payload / Response |
|--------|------|--------------------|
| `GET`    | `/api/v1/applications`        | → `ApplicationResponse[]`                        |
| `POST`   | `/api/v1/applications`        | [ApplicationCreate](file:///e:/Github/HyprCourse/Project/config-service/app/applications/models.py#10-13) → [ApplicationResponse](file:///e:/Github/HyprCourse/Project/config-service/app/applications/models.py#20-24) 201  |
| `PUT`    | `/api/v1/applications/{id}`   | [ApplicationUpdate](file:///e:/Github/HyprCourse/Project/config-service/app/applications/models.py#15-18) → [ApplicationResponse](file:///e:/Github/HyprCourse/Project/config-service/app/applications/models.py#20-24)      |
| `GET`    | `/api/v1/applications/{id}`   | → [ApplicationResponse](file:///e:/Github/HyprCourse/Project/config-service/app/applications/models.py#20-24)                          |
| `POST`   | `/api/v1/configurations`      | [ConfigurationCreate](file:///e:/Github/HyprCourse/Project/config-service/app/configurations/models.py#12-17) → [ConfigurationResponse](file:///e:/Github/HyprCourse/Project/config-service/app/configurations/models.py#25-31) 201 |
| `PUT`    | `/api/v1/configurations/{id}` | [ConfigurationUpdate](file:///e:/Github/HyprCourse/Project/config-service/app/configurations/models.py#19-23) → [ConfigurationResponse](file:///e:/Github/HyprCourse/Project/config-service/app/configurations/models.py#25-31)  |
| `GET`    | `/api/v1/configurations/{id}` | → [ConfigurationResponse](file:///e:/Github/HyprCourse/Project/config-service/app/configurations/models.py#25-31)                        |
| `GET`    | `/health`                     | → `{ status: "ok" }`                             |

**Error shapes:** `404 → { detail: string }`, `409 → { detail: string }`.

> [!NOTE]
> There is no `GET /api/v1/configurations` list endpoint. The UI resolves configurations via a **waterfall fetch**: `GET /applications/{id}` returns `configuration_ids[]`, then each ID is fetched individually via `GET /configurations/{id}`. This is acknowledged as **inefficient**; adding a bulk `GET /configurations?application_id=X` is planned as a **Collaborative Improvement** once the baseline is working.

---

## Resolved Design Decisions

| # | Question | Answer | Impact |
|---|----------|--------|--------|
| 1 | **Config listing** | Waterfall: `GET /applications/{id}` for IDs → `GET /configurations/{id}` per ID | `ApiClient.getConfigurationsForApp(appId)` runs `Promise.all()` on IDs; bulk endpoint is a future improvement |
| 2 | **Authentication** | None in this phase; future feature only | `ApiClient` is built without auth interceptor; a single hook point will be stubbed for later |
| 3 | **Deployment** | UI on `http://localhost:3000`, API on `http://localhost:8000`, deployed separately | Vite `server.proxy` routes `/api` → backend in dev; FastAPI CORS must allow `http://localhost:3000` |

---

## Proposed File & Folder Structure

```
ui/
├── README.md                      # ★ Project-level docs: setup, dev server, test commands, CORS gotcha
├── package.json
├── pnpm-lock.yaml
├── tsconfig.json
├── vite.config.ts
├── vitest.config.ts
├── playwright.config.ts
│
├── src/
│   ├── main.ts                    # Entry point — registers all components, mounts <app-shell>
│   │
│   ├── api/
│   │   ├── README.md              # ★ ApiClient: purpose, base URL config, error handling, auth stub
│   │   ├── client.ts              # ApiClient: typed fetch wrapper
│   │   └── types.ts               # TypeScript interfaces matching Pydantic models
│   │
│   ├── store/
│   │   ├── README.md              # ★ AppStore: state shape, events emitted, subscribe/unsubscribe pattern
│   │   └── app-store.ts           # AppStore: reactive state + EventTarget-based event bus
│   │
│   ├── components/
│   │   ├── app-shell/
│   │   │   ├── README.md          # ★ Attributes, slots, emitted events, gotchas
│   │   │   ├── app-shell.ts       # Root layout shell: sidebar + main content area
│   │   │   └── app-shell.css      # Scoped styles (inlined into Shadow DOM)
│   │   ├── app-list/
│   │   │   ├── README.md          # ★ Attributes, slots, emitted events, gotchas
│   │   │   ├── app-list.ts        # Lists all applications; emits 'app-selected' event
│   │   │   └── app-list.css
│   │   ├── app-form/
│   │   │   ├── README.md          # ★ Attributes, slots, emitted events, gotchas
│   │   │   ├── app-form.ts        # Create / Edit application form
│   │   │   └── app-form.css
│   │   ├── config-list/
│   │   │   ├── README.md          # ★ Attributes, slots, emitted events, gotchas
│   │   │   ├── config-list.ts     # Lists configurations for selected app (waterfall fetch)
│   │   │   └── config-list.css
│   │   ├── config-form/
│   │   │   ├── README.md          # ★ Attributes, slots, emitted events, gotchas
│   │   │   ├── config-form.ts     # Create / Edit configuration; includes JSON editor for `config`
│   │   │   └── config-form.css
│   │   └── toast-notification/
│   │       ├── README.md          # ★ Attributes, slots, emitted events, gotchas
│   │       ├── toast-notification.ts  # Success/error toast overlay
│   │       └── toast-notification.css
│   │
│   └── styles/
│       └── tokens.css             # Global CSS custom properties (design tokens)
│
├── tests/
│   ├── unit/
│   │   ├── api/
│   │   │   └── client.test.ts     # Vitest: mocked fetch tests for ApiClient
│   │   └── store/
│   │       └── app-store.test.ts  # Vitest: state mutation and event emission tests
│   └── e2e/
│       ├── applications.spec.ts   # Playwright: full CRUD flow for applications
│       └── configurations.spec.ts # Playwright: full CRUD flow for configurations
│
└── index.html                     # Root HTML shell; loads main.ts as ES module
```

> [!NOTE]
> Files marked ★ are **required documentation** per [agents.md](file:///e:/Github/HyprCourse/Project/agents.md). They must be created alongside the code, not after.

---

## Documentation Requirements ([agents.md](file:///e:/Github/HyprCourse/Project/agents.md) compliance)

Every [README.md](file:///e:/Github/HyprCourse/Project/README.md) marked ★ above must cover the following sections:

| Section | Content |
|---------|---------|
| **Purpose** | What this module/component does and why it exists |
| **Inputs** | Observed HTML attributes, constructor args, or store events it reads |
| **Outputs** | Custom events dispatched (name, `detail` shape), return values |
| **Dependencies** | What it imports (store, API client, other components) |
| **Usage Example** | Minimal HTML or TypeScript snippet showing it in use |
| **Gotchas** | Known edge cases (e.g. waterfall fetch latency, Shadow DOM CSS inheritance) |

**`ui/README.md`** (root-level) must additionally include:
- Prerequisites (`Node`, `pnpm` version)
- PowerShell setup commands (`pnpm install`, `pnpm dev`)
- How to start the backend (`uvicorn app.main:app --host 127.0.0.1 --port 8000`)
- CORS explanation and the Vite proxy setup
- Test commands (`pnpm test:unit`, `pnpm test:e2e`)

---

## pnpm Dependencies

### Runtime (`dependencies`)
> The UI has **zero** runtime dependencies — it ships only Web Components and native browser APIs.

### Development (`devDependencies`)

| Package | Version | Purpose |
|---------|---------|---------|
| `typescript` | `^5.9.2` | TypeScript compiler (strict mode) |
| `vite` | `^5.4.0` | Dev server + ESM bundler |
| `@vitejs/plugin-basic-ssl` | `^1.1.0` | Optional HTTPS in dev (if needed) |
| `vitest` | `^2.1.0` | Unit test runner (Vite-native) |
| `@vitest/coverage-v8` | `^2.1.0` | Code coverage reporter |
| `jsdom` | `^25.0.0` | DOM environment for Vitest |
| `@playwright/test` | `^1.47.0` | End-to-end / integration testing |
| `vite-plugin-dts` | `^4.3.0` | TypeScript declaration file generation (if publishing) |

**Install command:**
```bash
pnpm add -D typescript@^5.9.2 vite@^5.4.0 vitest@^2.1.0 @vitest/coverage-v8@^2.1.0 jsdom@^25.0.0 @playwright/test@^1.47.0
```

---

## State Management Strategy

No external state library (Redux, MobX, etc.) is used. The architecture uses three complementary native patterns:

### 1. Centralised `AppStore` (singleton)

A plain TypeScript class exported as a module-level singleton. It holds the canonical in-memory state and exposes typed mutation methods.

```typescript
// src/store/app-store.ts  (simplified)
class AppStore extends EventTarget {
  #applications: ApplicationResponse[] = [];
  #selectedAppId: string | null = null;

  get applications() { return this.#applications; }

  setApplications(apps: ApplicationResponse[]) {
    this.#applications = apps;
    this.dispatchEvent(new CustomEvent('applications-changed', { detail: apps }));
  }

  selectApplication(id: string) {
    this.#selectedAppId = id;
    this.dispatchEvent(new CustomEvent('app-selected', { detail: id }));
  }
}

export const store = new AppStore();
```

### 2. Native `EventTarget` as Event Bus

`AppStore extends EventTarget`. Components subscribe to store events in `connectedCallback` and unsubscribe in `disconnectedCallback`, keeping memory clean.

```typescript
// Inside a Web Component
connectedCallback() {
  store.addEventListener('applications-changed', this.#onAppsChanged);
}
disconnectedCallback() {
  store.removeEventListener('applications-changed', this.#onAppsChanged);
}
```

### 3. DOM Custom Events for Child → Parent Communication

Child components emit typed `CustomEvent`s that bubble through the Shadow DOM boundary using `composed: true`. Parent components listen on the host element.

```typescript
// Child emitting upward  
this.dispatchEvent(new CustomEvent('app-selected', {
  detail: { id },
  bubbles: true,
  composed: true,
}));
```

**Data flow summary:**

```
API ──fetch──▶ ApiClient ──▶ AppStore (mutate + dispatch event)
                                    │
                         EventTarget listeners
                                    │
                         Web Components re-render
                                    │
            (user action) CustomEvent bubbles up ──▶ parent handles
```

---

## CSS Design System Strategy

All design tokens are defined as **CSS Custom Properties** in `src/styles/tokens.css`, which is imported globally via `index.html`. Shadow DOM components inherit these tokens through the CSS cascade.

```css
/* src/styles/tokens.css */
:root {
  /* Colour palette */
  --color-bg-base:       #0f1117;
  --color-bg-surface:    #1a1d27;
  --color-bg-elevated:   #252836;
  --color-border:        #2e3144;
  --color-accent:        #6c8fff;
  --color-accent-hover:  #8ba4ff;
  --color-text-primary:  #e2e4f0;
  --color-text-muted:    #8b90a0;
  --color-success:       #4caf87;
  --color-error:         #e06c75;
  --color-warning:       #e5c07b;

  /* Typography */
  --font-family-base:  'Inter', system-ui, sans-serif;
  --font-size-sm:      0.8125rem;  /* 13px */
  --font-size-base:    0.9375rem;  /* 15px */
  --font-size-lg:      1.125rem;   /* 18px */
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-bold:   700;

  /* Spacing scale (4px base) */
  --space-1: 0.25rem;
  --space-2: 0.5rem;
  --space-3: 0.75rem;
  --space-4: 1rem;
  --space-6: 1.5rem;
  --space-8: 2rem;

  /* Borders */
  --radius-sm:  6px;
  --radius-md:  10px;
  --radius-lg:  16px;
  --border-1:   1px solid var(--color-border);

  /* Shadows */
  --shadow-card:  0 4px 24px rgba(0,0,0,0.35);
  --shadow-toast: 0 8px 32px rgba(0,0,0,0.5);

  /* Transitions */
  --transition-fast:   150ms ease;
  --transition-normal: 250ms ease;
}
```

> [!TIP]
> CSS Custom Properties **pierce the Shadow DOM boundary** — child components can consume `:root` tokens freely. Component-specific overrides can be exposed as `--component-name-*` properties for theming from outside.

---

## Verification Plan

### Unit Tests (Vitest)

Run with:
```bash
cd ui
pnpm test:unit
```

Defined in `vitest.config.ts` with `environment: 'jsdom'`.

| Test File | What it covers |
|-----------|----------------|
| `tests/unit/api/client.test.ts` | `ApiClient` fetch calls: correct URL construction, correct HTTP verbs, correct JSON serialisation, 404/409 error parsing, network error handling. Uses `vi.stubGlobal('fetch', mockFetch)`. |
| `tests/unit/store/app-store.test.ts` | `AppStore` state mutations: `setApplications` populates state and dispatches `applications-changed` event; `selectApplication` updates selection and dispatches `app-selected` event. |

### Integration / E2E Tests (Playwright)

**Prerequisite**: The config-service backend must be running on `http://127.0.0.1:8000`. Start with:
```bash
cd config-service
uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Run Playwright tests with:
```bash
cd ui
pnpm test:e2e
```

| Test File | Scenario |
|-----------|----------|
| `tests/e2e/applications.spec.ts` | Create app → list shows new app → edit app name → verify updated name in list |
| `tests/e2e/configurations.spec.ts` | Select app → create config with JSON payload → config appears in list → edit config → verify changes |

### Manual Smoke Test
1. Start the backend: `uvicorn app.main:app --host 127.0.0.1 --port 8000`
2. Start the UI dev server: `pnpm dev` (opens at `http://localhost:3000`)
3. Verify the application list loads with no console errors
4. Create a new application — confirm the success toast appears and the new entry appears in the list
5. Click the application to view its configurations
6. Create a new configuration with a valid JSON object in the [config](file:///e:/Github/HyprCourse/Project/config-service/app/configurations/router.py#30-33) field
7. Verify the configuration appears in the list
8. Edit the configuration and change the `name` — verify the updated name is reflected

---

## Required Backend Change: CORS

> [!IMPORTANT]
> Because the UI (`localhost:3000`) and API (`localhost:8000`) are on different origins, FastAPI must have CORS enabled **before the UI can make requests**. Add `fastapi[all]` is already installed; the following must be added to [app/main.py](file:///e:/Github/HyprCourse/Project/config-service/app/main.py):

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)
```

## Collaborative Improvement (Post-Baseline)

Once the baseline UI is working, the following backend endpoint should be added to eliminate the waterfall fetch:
```
GET /api/v1/configurations?application_id={id}  →  ConfigurationResponse[]
```
The `ApiClient` is designed to make swapping the implementation trivial.
