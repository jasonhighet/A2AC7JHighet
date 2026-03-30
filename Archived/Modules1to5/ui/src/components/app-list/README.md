# `<app-list>` Component

Sidebar list of all applications.

## Purpose
Renders the application list from the store, highlights the selected app, and allows navigation (click to select) and editing (click the pencil icon).

## Inputs (Observed Attributes)
None — reacts to store events only.

## Outputs (Emitted Events)
| Event | `composed` | `detail` | When |
|-------|-----------|---------|------|
| `edit-app` | ✅ | `ApplicationResponse` | User clicks the edit icon on an app |

## Dependencies
- `store` — subscribes to `applications-changed`, `app-selected`

## Usage Example
```html
<app-list id="appList"></app-list>

<script type="module">
  document.querySelector('app-list').addEventListener('edit-app', (e) => {
    console.log('Edit requested for:', e.detail);
  });
</script>
```

## Gotchas
- Clicking the row body selects the app (`store.selectApplication`); clicking the edit button emits `edit-app` and stops propagation.
- The list re-renders fully on each `applications-changed` event (no virtual DOM diffing).
