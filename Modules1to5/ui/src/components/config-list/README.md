# `<config-list>` Component

Responsive grid of configuration cards for the selected application.

## Purpose
Displays all configurations for the currently selected application as rich cards. Each card shows the config name, comments, a key count badge, and a JSON preview. An edit button emits an event for the form to open.

## Inputs (Observed Attributes)
None — reacts to store events only.

## Outputs (Emitted Events)
| Event | `composed` | `detail` | When |
|-------|-----------|---------|------|
| `edit-config` | ✅ | `ConfigurationResponse` | User clicks the Edit button on a card |

## Dependencies
- `store` — subscribes to `configs-changed`, `app-selected`

## Usage Example
```html
<config-list id="configList"></config-list>
```

## Gotchas
- The component renders an empty state when `store.selectedAppId` is null.
- If `configuration_ids` on the app is empty or the waterfall fetch returns nothing, the "no configurations yet" empty state is shown.
- JSON preview is capped at `max-height: 120px` with scroll; very large config objects are truncated visually.
