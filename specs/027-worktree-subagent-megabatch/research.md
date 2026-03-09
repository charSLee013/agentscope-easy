# Research Notes: 027 worktree subagent megabatch closeout

## Why this approach

The repeated small-branch workflow caused high context switching and frequent
CI rework loops. A worktree + subagent fan-out/fan-in workflow keeps each lane
isolated while preserving a single integration choke point.

## Practical observations

1. Lane isolation sharply reduced conflict blast radius.
2. Many upstream fixes were already semantically covered on easy baseline,
   leading to safe empty-skips.
3. Integration-level validation must be mandatory because lane-green does not
   guarantee global-green.

## Conflict handling policy

- Keep easy baseline behavior first.
- Apply only L1 fix intent from upstream commit.
- Skip version or architecture drift changes.
