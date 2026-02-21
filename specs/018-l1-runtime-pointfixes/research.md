# Research Notes

## Decision 1: Batch composition
- **Decision**: Use only direct-applicable commits with low conflict risk.
- **Rationale**: Maximize throughput and minimize repeated branch overhead.
- **Alternatives considered**: Include additional conflict-heavy commits.

## Decision 2: Test-file restoration
- **Decision**: Restore `tests/token_huggingface_test.py` immediately.
- **Rationale**: Deletion was collateral to one cherry-pick and outside batch intent.
- **Alternatives considered**: Keep deletion and defer restoration.
