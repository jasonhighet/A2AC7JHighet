# `<toast-notification>` Component

Animated slide-in toast for success and error feedback.

## Purpose
Provides a fixed-position, auto-dismissing notification overlay. Called imperatively by `app-shell` to show success or error messages after API operations.

## Inputs (Observed Attributes)
None.

## Public Methods
| Method | Signature | Purpose |
|--------|-----------|---------|
| `show(message, type)` | `(msg: string, type: 'success' \| 'error' \| 'info') => void` | Display the toast |

## Outputs (Emitted Events)
None.

## Usage Example
```typescript
const toast = shadow.getElementById('toast') as ToastNotification;
toast.show('Application created.', 'success');
toast.show('Name already exists.', 'error');
```

## Gotchas
- If `show()` is called while a toast is already visible, the existing timer is cancelled and the new message replaces it immediately.
- Auto-dismisses after 4 seconds. Users can also click ✕ to dismiss early.
- Colour differentiation is via border colour only (success = green border, error = red border).
