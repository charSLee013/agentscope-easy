# Research: Equivalence and supersession proof for 08be504 / 7df0148 / 2984902

## Decision 1: Keep this batch docs-only

- **Decision**: No runtime code changes; close via evidence documentation.
- **Rationale**: Two targets are already absorbed and one is superseded by a
  higher version on easy.
- **Alternatives considered**:
  - Re-apply commits directly (would duplicate history and risk regressions).
  - Force version rollback to match upstream intermediate state (incorrect).

## Evidence A: `08be504` (version -> 1.0.9)

- **Target intent**: set `src/agentscope/_version.py` to `1.0.9`.
- **Current easy state**: `_version.py` is `1.0.10`.
- **Decision**: **superseded** (do not downgrade version).

## Evidence B: `7df0148` (OpenTelemetry version constraints)

- **Target intent**:
  - `opentelemetry-api>=1.39.0`
  - `opentelemetry-sdk>=1.39.0`
  - `opentelemetry-exporter-otlp>=1.39.0`
  - `opentelemetry-semantic-conventions>=0.60b0`
- **Current easy state**: all constraints already present in
  `pyproject.toml`.
- **Decision**: **already-absorbed**.

## Evidence C: `2984902` (mem0 pin)

- **Target intent**: pin `mem0ai<=0.1.116` to avoid upstream bug.
- **Current easy state**: `mem0ai<=0.1.116` already present in optional deps
  (`full` and `dev`) in `pyproject.toml`.
- **Decision**: **already-absorbed**.

## Final outcome

All three requested low-risk targets are resolved without code modifications:

- `08be504`: superseded
- `7df0148`: already-absorbed
- `2984902`: already-absorbed
