# Data Model: 019 L1 fast closeout A

This batch does not introduce runtime data schema changes. The only data
artifacts are process/audit records in specs files.

## Entities

## 1) AbsorptionCandidate

- `commit_sha` (string): upstream commit id
- `topic` (string): short topic label
- `result` (enum): `applied` | `empty_skipped` | `conflicted_resolved`
- `notes` (string): rationale and conflict details

## 2) ValidationRun

- `gate` (string): command or check name
- `status` (enum): `pass` | `fail`
- `details` (string): key output summary

## 3) ChecklistItem

- `id` (string)
- `description` (string)
- `done` (boolean)
- `evidence` (string)
