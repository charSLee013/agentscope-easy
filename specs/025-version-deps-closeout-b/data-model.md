# Data Model: 025 version deps closeout b

## Entities

### BatchCommit
- `hash`: upstream commit id
- `title`: short summary
- `status`: `applied | empty-skipped | conflict-safe-skipped`
- `reason`: outcome rationale

### EquivalenceEvidence
- `upstream_hash`: original commit
- `easy_hash`: local equivalent commit
- `scope`: dependency/version coverage

### ValidationEvidence
- `command`: executed command
- `result`: pass/fail
- `notes`: optional details
