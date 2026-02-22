# Data Model: 026 toolkit l1 closeout

## Entities

### BatchCommit
- `hash`: upstream commit id
- `status`: `applied | empty-skipped | conflict-safe-skipped | selective-applied`
- `reason`: final decision rationale

### ConflictResolution
- `included_files`: files with migrated fix semantics
- `excluded_files`: noisy files intentionally kept from easy baseline

### ValidationEvidence
- `command`: executed verification command
- `result`: pass/fail
- `notes`: execution details
