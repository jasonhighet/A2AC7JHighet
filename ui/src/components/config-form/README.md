# `<config-form>` Component

Modal form for creating and editing configurations.

## Purpose
Like `app-form`, but for configurations. Includes an inline JSON editor (monospace textarea) for the `config` JSONB field with real-time parse validation.

## Inputs (Observed Attributes)
None — controlled imperatively via public methods.

## Public Methods
| Method | Signature | Purpose |
|--------|-----------|---------|
| `resetForApp(appId)` | `(appId: string) => void` | Clear form for creating a new config under `appId` |
| `loadConfig(cfg)` | `(cfg: ConfigurationResponse) => void` | Prefill form for editing |

## Outputs (Emitted Events)
| Event | `composed` | `detail` | When |
|-------|-----------|---------|------|
| `form-close` | ✅ | none | User clicks Cancel |
| `form-success` | ✅ | `string` (success message) | API call succeeded |

## Dependencies
- `store.createConfiguration()` / `store.updateConfiguration()`

## Gotchas
- The JSON field only accepts a JSON **object** (not arrays, strings, or `null`). The validator rejects non-objects.
- The submit button is disabled if JSON is invalid.
- `loadConfig()` pretty-prints the existing config via `JSON.stringify(config, null, 2)` for editing.
