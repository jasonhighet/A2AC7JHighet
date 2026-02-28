# `<app-shell>` Component

Root layout shell. Owns the two-column layout and orchestrates all child components.

## Purpose
Provides the page structure (sidebar + main area), opens/closes modals, shows the loading bar and toast notifications, and wires child component events to store actions.

## Inputs (Observed Attributes)
None.

## Outputs (Emitted Events)
None — app-shell is the root; events bubble into it, not out of it.

## Dependencies
- `store` — subscribes to `loading-changed`, `error-changed`, `app-selected`
- Child components: `<app-list>`, `<app-form>`, `<config-list>`, `<config-form>`, `<toast-notification>`

## Usage Example
```html
<!-- index.html -->
<app-shell></app-shell>
<script type="module" src="/src/main.ts"></script>
```

## Gotchas
- Modals are closed by clicking the overlay backdrop or when a `form-success` event fires.
- The "New Configuration" button is hidden until an application is selected.
