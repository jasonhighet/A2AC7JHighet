# API Client (`src/api/`)

Typed `fetch` wrapper over the Config Service REST API.

---

## Purpose

Centralises all HTTP calls to the backend into two typed namespaces (`applicationsApi`, `configurationsApi`). All methods return typed Promises and throw `ApiClientError` on non-2xx responses.

## Files

| File | Purpose |
|------|---------|
| `client.ts` | Fetch wrapper, API method namespaces, `ApiClientError` |
| `types.ts` | TypeScript interfaces mirroring Pydantic models |

## Inputs

None — all methods accept typed request bodies as arguments.

## Outputs

All methods return `Promise<TypedResponse>` and throw `ApiClientError` on failure.

```typescript
export class ApiClientError extends Error {
  status: number;   // HTTP status code (e.g. 404, 409)
  detail: string;   // Message from { detail: string } response body
}
```

## Base URL

`/api/v1` — a relative path so the Vite proxy forwards to `localhost:8000` in dev.

## Auth Stub

```typescript
// client.ts — update this function when auth is introduced
function getAuthHeaders(): Record<string, string> {
  // TODO(auth): return { Authorization: `Bearer ${getToken()}` }
  return {};
}
```

## Usage Example

```typescript
import { applicationsApi, ApiClientError } from './api/client.js';

try {
  const apps = await applicationsApi.list();
} catch (err) {
  if (err instanceof ApiClientError) {
    console.error(err.status, err.detail);
  }
}
```

## Gotchas

- `getMany(ids)` runs `Promise.all` — a single failing ID rejects the entire batch.
- The client does not retry on failure — implement retry logic at the call site if needed.
