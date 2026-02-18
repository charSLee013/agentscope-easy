# Research Notes

## Decision 1: Batch strategy
- **Decision**: Use one low-risk bulk branch with direct-applicable commits.
- **Rationale**: Maximizes throughput while minimizing manual conflict work.
- **Alternatives considered**: Smaller one-commit branches (higher overhead).

## Decision 2: Conflict handling
- **Decision**: Defer conflict-heavy commits to later dedicated batches.
- **Rationale**: Prevent long tail delays for this fast-closeout branch.
- **Alternatives considered**: Manual backport in current batch.
