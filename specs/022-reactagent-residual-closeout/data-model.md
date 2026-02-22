# Data Model: 022 reactagent residual closeout

## Entities

### BatchCommit
- `hash`: upstream commit id
- `title`: short description
- `status`: `applied | empty-skipped | conflict-safe-skipped`
- `reason`: why this status is chosen

### ValidationEvidence
- `command`: executed validation command
- `result`: pass/fail
- `notes`: fallback or environment notes
