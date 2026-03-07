# Data Model: 027 worktree subagent megabatch closeout

No business-domain model changes are introduced. Tracking entities for
absorption and verification:

## 1) CommitAllocation

- `sha` (string)
- `lane` (enum): `A` | `B` | `C` | `D`
- `status` (enum): `applied` | `skipped-empty` | `skipped-safe`
- `note` (string)

## 2) LaneValidation

- `lane` (string)
- `pre_commit` (enum): `pass` | `fail`
- `ruff` (enum): `pass` | `fail`
- `pytest` (enum): `pass` | `fail`
- `risk` (string)

## 3) IntegrationValidation

- `command` (string)
- `result` (enum): `pass` | `fail`
- `evidence` (string)
