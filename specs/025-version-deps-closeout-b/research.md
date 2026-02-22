# Research Notes: 025 version deps closeout b

## Selection logic

This batch focuses on dependency/version lane only to maintain low risk and
high throughput.

## Per-commit status

- `2984902` -> empty-skipped. Equivalent already exists in easy via `17b4b08`
  (`mem0ai<=0.1.116`).
- `7df0148` -> empty-skipped. Equivalent already exists in easy via `17b4b08`
  (OpenTelemetry baseline versions).
- `08be504` -> conflict-safe-skipped. Commit sets version to `1.0.9`, but easy
  baseline is `1.0.10` (`0def94a`), so applying would be a downgrade.

## Risk decision

Version downgrade is disallowed in this closeout lane; keep baseline as-is.
