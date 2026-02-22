# Data Model: 024 model l1 fix batch

## Entities

### BatchCommit
- `hash`: upstream commit id
- `title`: short description
- `status`: `applied | empty-skipped | conflict-safe-skipped`
- `reason`: outcome rationale

### ValidationEvidence
- `command`: executed command
- `result`: pass/fail
- `notes`: optional detail
