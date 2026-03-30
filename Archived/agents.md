# Project Rules

## Environment

- This is a **native Windows environment**. Do NOT use Linux/macOS/Docker paths, commands, or assumptions.
- Use PowerShell syntax for any shell commands (e.g. `$env:VAR`, backslash paths, `Get-ChildItem` not `ls`).
- File paths use Windows conventions (e.g. `e:\Github\HyprCourse\Project`).

## Documentation

- Always write **technical documentation** alongside any new code, feature, or module.
- Documentation should be written as Markdown files co-located with the code they describe, or updated in the relevant `README.md`.
- Document: purpose, inputs/outputs, dependencies, usage examples, and any gotchas.

## Testing

- Always write **unit tests** for any new functions, classes, or modules.
- Tests should live in a `tests/` directory mirroring the source structure.
- Use the testing framework already present in the project; do not introduce a new one without discussion.
- Tests must be runnable and passing before marking any task complete.
