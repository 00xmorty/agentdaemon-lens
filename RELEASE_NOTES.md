# v0.2.0

- Compare two saved schema-1 JSON inventories with `--compare BEFORE AFTER`.
- Signed aggregate deltas for release directories, regular files and logical bytes.
- Strict offline comparison: no process probe or package traversal; incompatible acquisition flags are rejected.
- UNKNOWN/skipped-link families have null deltas. Check mode prioritizes incomplete evidence over changes.
- Validate fixed family labels, states and bounded nonnegative integer counters; no extra input values are echoed.
- Retains v0.1.0 inventory output and read-only safety boundaries.
- 25 unit/CLI tests, including positive/negative deltas, reordered families, invalid snapshots, no-live-probe assertions and check-code precedence.

Comparability of machine/root/permissions is the operator's responsibility. No process comparison, content identity, reclaimed-space, cleanup or user-success claim.

# v0.1.0

Initial safe, narrow release:
- Aggregate release-directory count and logical bytes for two known Codex package families.
- Value-free lexical managed-daemon and updater process counts.
- Strict offline saved-process-input mode, JSON and check exit statuses.
- No network, process termination, settings changes, cleanup or repair.
- Symlink skipping, entry/time budgets, permission-failure UNKNOWN, hardlink deduplication.
- Synthetic fixtures exercise the real CLI; CI covers macOS/Linux and Python 3.9/3.13.

No launchd ownership, orphan proof, exact duplicate detection or reclaimable-space claim. No successful user outcome measured.
