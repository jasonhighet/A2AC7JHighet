# AppStore (`src/store/`)

Centralised reactive state container for the Admin UI.

---

## Purpose

`AppStore` is a singleton class that extends `EventTarget`. It holds all application and configuration state, exposes typed mutation methods, and notifies subscribers via `CustomEvent` when state changes.

## Inputs (store reads)

None directly — state is mutated via method calls.

## Outputs (events dispatched)

| Event | `detail` type | When fired |
|-------|--------------|------------|
| `applications-changed` | `ApplicationResponse[]` | After load, create, or update |
| `app-selected` | `string \| null` | When `selectApplication()` is called |
| `configs-changed` | `ConfigurationResponse[]` | After configs load, create, or update |
| `loading-changed` | `boolean` | Before and after any async operation |
| `error-changed` | `string \| null` | When an API call fails |

## Usage Example

```typescript
import { store } from '../store/app-store.js';

class MyComponent extends HTMLElement {
  #onAppsChanged = (e: Event) => {
    const apps = (e as CustomEvent<ApplicationResponse[]>).detail;
    this.#render(apps);
  };

  connectedCallback() {
    store.addEventListener('applications-changed', this.#onAppsChanged);
    void store.loadApplications();
  }

  disconnectedCallback() {
    store.removeEventListener('applications-changed', this.#onAppsChanged);
  }
}
```

## Gotchas

- Always unsubscribe in `disconnectedCallback()` to prevent memory leaks.
- `selectApplication(id)` immediately triggers a waterfall fetch for configs — loading events will fire.
- `store.error` is set on the store instance but also dispatched via `error-changed`. The `app-shell` listens for `error-changed` to show the toast.
