# `<app-form>` Component

Modal form for creating and editing applications.

## Purpose
Renders a styled card form inside the modal overlay managed by `app-shell`. Supports both create and edit modes via its public API.

## Inputs (Observed Attributes)
None — controlled imperatively via public methods.

## Public Methods
| Method | Signature | Purpose |
|--------|-----------|---------|
| `reset()` | `() => void` | Clear form for creating a new application |
| `loadApp(app)` | `(app: ApplicationResponse) => void` | Prefill form for editing |

## Outputs (Emitted Events)
| Event | `composed` | `detail` | When |
|-------|-----------|---------|------|
| `form-close` | ✅ | none | User clicks Cancel |
| `form-success` | ✅ | `string` (success message) | API call succeeded |

## Dependencies
- `store.createApplication()` / `store.updateApplication()`

## Usage Example
```typescript
const form = shadow.getElementById('appForm') as AppForm;
form.reset();          // new app
form.loadApp(myApp);   // edit existing
```

## Gotchas
- Inline validation error is shown inside the card (below the fields), not via the global toast.
- The submit button is disabled during the API call to prevent double-submission.
