# Instructions: Admin UI Implementation Plan

Act as a Senior Frontend Engineer. Your goal is to create a comprehensive implementation plan for a web-based Admin Interface that manages the Configuration Service.

## Core Features
- **Application Management**: View, add, and update application entries.
- **Configuration Management**: View, add, and update name/value pairs (stored as JSONB) for specific applications.

## Technical Constraints (Strict Adherence Required)
- **Reference**: Use `@config-service/svc/api/endpoints.py` to understand the available FastAPI endpoints and Pydantic payloads.
- **Package Manager**: Use `pnpm` to manage dependencies and scripts.
- **Languages**: Strictly TypeScript 5.9.2, HTML, and CSS. No direct JavaScript.
- **Frameworks**: NO external frameworks (No React, No Vue, No Svelte). 
- **Architecture**: Use native Web Components and the browser's native Shadow DOM.
- **Networking**: Use only the modern `fetch` API for all HTTP calls.
- **Testing**: Include a plan for unit testing with `vitest` and integration testing with `Playwright`.

## Deliverables
Please provide a plan that includes:
1. Proposed file and folder structure within the `ui/` directory.
2. A list of necessary `pnpm` dependencies with version numbers.
3. A strategy for state management and communication between Web Components without an external library.
4. A standard look-and-feel strategy using CSS variables.

## Known Constraints & Decisions

These questions have already been answered — do not ask them again.

1. **Configuration Listing**: There is no `GET /configurations?application_id=X` endpoint. The UI must use a waterfall fetch: call `GET /applications/{id}` to retrieve the list of `configuration_ids`, then fetch each one individually via `GET /configurations/{id}` using `Promise.all()`. Acknowledge this is inefficient and treat adding a bulk fetch endpoint as a future "Collaborative Improvement" once the baseline is working.

2. **Authentication**: No authentication headers are required for this phase. The API is open. Do not implement an auth interceptor, but leave a single clearly-commented stub/hook in the `ApiClient` for future use.

3. **Deployment**: The UI and API are deployed **separately**.
   - UI dev server: `http://localhost:3000` (Vite)
   - API: `http://localhost:8000` (Uvicorn)
   - Configure Vite's `server.proxy` to route `/api` → `http://localhost:8000` in development.
   - The FastAPI backend requires `CORSMiddleware` allowing `http://localhost:3000` before any browser requests will succeed.