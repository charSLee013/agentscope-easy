# Data Model: 020 docs/example megabatch

No new runtime domain model is introduced by this batch. The data entities
below are tracking/audit entities for absorption work.

## Entities

## 1) AbsorbedCommit

- `sha` (string): upstream commit sha
- `topic` (string): commit title
- `status` (enum): `applied` | `empty_skipped`
- `conflict_files` (list[string]): files that needed resolution
- `resolution_note` (string): how conflict was resolved

## 2) ValidationGate

- `name` (string): gate command/check
- `status` (enum): `pass` | `fail`
- `evidence` (string): concise output summary

## 3) BatchDecision

- `rule_id` (string): fixed resolution rule identifier
- `scope` (string): affected file class (e.g., README/version/prompt)
- `decision` (string): chosen strategy
