# Data Model: 023 l1 fast closeout b

## Entities

### BatchCommit
- `hash`: upstream commit id
- `title`: short description
- `status`: `applied | empty-skipped | conflict-safe-skipped`
- `reason`: decision rationale

### ValidationEvidence
- `command`: executed verification command
- `result`: pass/fail
- `notes`: optional execution notes
